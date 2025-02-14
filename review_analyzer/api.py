from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple
import networkx as nx
import pandas as pd
import os
import numpy as np
from collections import defaultdict
from decimal import Decimal

app = FastAPI(title="Hotel Recommendation API")

# CORS ayarlarını ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm originlere izin ver
    allow_credentials=True,
    allow_methods=["*"],  # Tüm HTTP metodlarına izin ver
    allow_headers=["*"],  # Tüm headerlara izin ver
)

# Load data once at startup
try:
    # Create an empty graph
    G = nx.Graph()
    
    # Veri dosyalarının yolunu düzelt
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'graph_nodes_edges')
    
    # Load all nodes
    node_types = {
        'Hotel': ('hotel_nodes_2.csv', 'hotel_id'),
        'Experience': ('experience_nodes.csv', 'experience_id'),
        'Location': ('location_nodes.csv', 'location_id'),
        'User': ('user_nodes.csv', None)
    }

    for node_type, (filename, id_field) in node_types.items():
        df = pd.read_csv(os.path.join(data_path, filename), encoding='iso-8859-9')
        for _, row in df.iterrows():
            node_data = {'type': node_type}
            for col in df.columns:
                if pd.notna(row[col]):
                    node_data[col] = row[col]
            G.add_node(row['id'], **node_data)

    # Load all edges
    edge_types = {
        'has_experience': 'has_experience_edges.csv',
        'likes': 'likes_edges.csv',
        'located_in': 'located_in_edges.csv',
        'stayed_at': 'stayed_at_edges.csv'
    }

    for edge_type, filename in edge_types.items():
        edge_df = pd.read_csv(os.path.join(data_path, filename), encoding='iso-8859-9')
        for _, row in edge_df.iterrows():
            G.add_edge(
                row['source'],
                row['target'],
                relationship_type=edge_type.upper(),
                rating=row.get('rating', 0)
            )

except Exception as e:
    print(f"Data loading error: {str(e)}")
    raise

# Pydantic models
class ExperiencePreference(BaseModel):
    experience_id: int
    importance: int

class RecommendationRequest(BaseModel):
    experience_preferences: List[ExperiencePreference]
    user_email: str = None

class ExperienceRating(BaseModel):
    rating: float
    importance: int

    class Config:
        json_encoders = {
            float: lambda v: round(v, 2)
        }

class HotelRecommendation(BaseModel):
    hotel_id: int
    name: str
    location: str
    rating: float
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 2)
        }

@app.get("/")
async def root():
    return {
        "message": "Hotel Recommendation API'ye Hoş Geldiniz",
        "status": "active",
        "nodes_count": G.number_of_nodes(),
        "edges_count": G.number_of_edges()
    }

@app.post("/recommend/", response_model=List[HotelRecommendation])
async def recommend_hotels(request: RecommendationRequest):
    try:
        experience_preferences = [
            (pref.experience_id, pref.importance) 
            for pref in request.experience_preferences
        ]
        
        recommendations = recommend_hotels_for_experiences(
            G, 
            experience_preferences, 
            request.user_email
        )
        
        if isinstance(recommendations, str):
            raise HTTPException(status_code=404, detail=recommendations)
        
        # Find the highest pagerank score
        max_pagerank = max(hotel['pagerank_score'] for hotel in recommendations)
        
        # Format results
        formatted_recommendations = []
        for hotel in recommendations:
            hotel_node = hotel['node_id']
            
            # Otelin bağlı olduğu lokasyonu bul
            location_name = ''
            for neighbor in G.neighbors(hotel_node):
                if (G.nodes[neighbor].get('type') == 'Location' and 
                    G[hotel_node][neighbor].get('relationship_type') == 'LOCATED_IN'):
                    location_name = G.nodes[neighbor].get('name', '')
                    break
            
            formatted_recommendations.append(HotelRecommendation(
                hotel_id=G.nodes[hotel_node].get('hotel_id'),
                name=hotel['name'],
                location=location_name,  # Bulunan lokasyon adını kullan
                rating=round(float(hotel['final_score']), 2)
            ))
        
        return formatted_recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experiences/")
async def get_experiences():
    """List all experiences"""
    experiences = []
    for node in G.nodes(data=True):
        if node[1].get('type') == 'Experience':
            experiences.append({
                'id': node[1].get('experience_id'),
                'name': node[1].get('name'),
                'description': node[1].get('description')
            })
    return experiences

@app.get("/hotels/{hotel_id}")
async def get_hotel_details(hotel_id: int):
    """Get details of a specific hotel"""
    for node in G.nodes(data=True):
        if (node[1].get('type') == 'Hotel' and 
            node[1].get('hotel_id') == hotel_id):
            return {
                'id': hotel_id,
                'name': node[1].get('name'),
                'rating': node[1].get('rating'),
                'experiences': [
                    {
                        'name': G.nodes[exp]['name'],
                        'rating': G[node[0]][exp]['rating']
                    }
                    for exp in G.neighbors(node[0])
                    if G.nodes[exp]['type'] == 'Experience'
                ]
            }
    raise HTTPException(status_code=404, detail="Hotel not found")

def calculate_weighted_pagerank(G):
    """Calculate weighted PageRank on the graph"""
    # Calculate PageRank using edge weights
    edge_weights = {(u, v): data.get('rating', 1.0) 
                   for u, v, data in G.edges(data=True)}
    
    return nx.pagerank(G, weight='rating')

def get_user_history(G, user_email):
    """Get user's hotel and experience history"""
    user_node = None
    for node in G.nodes():
        if (G.nodes[node].get('type') == 'User' and 
            G.nodes[node].get('email') == user_email):
            user_node = node
            break
    
    if not user_node:
        return None, None
    
    # User's hotel ratings
    hotel_ratings = {}
    # User's liked experiences
    liked_experiences = set()
    
    for neighbor in G.neighbors(user_node):
        if G.nodes[neighbor].get('type') == 'Hotel':
            hotel_ratings[neighbor] = G[user_node][neighbor].get('rating', 0)
        elif G.nodes[neighbor].get('type') == 'Experience':
            if G[user_node][neighbor].get('rating', 0) >= 4:
                liked_experiences.add(neighbor)
    
    return hotel_ratings, liked_experiences

def calculate_collaborative_score(G, hotel_node, user_hotel_ratings, user_liked_experiences):
    """Calculate collaborative filtering score"""
    if not user_hotel_ratings:
        return 0
    
    similar_users = []
    for user in G.nodes():
        if G.nodes[user].get('type') == 'User':
            similarity_score = 0
            
            # Hotel ratings similarity
            user_ratings = {}
            for hotel in G.neighbors(user):
                if G.nodes[hotel].get('type') == 'Hotel':
                    if G[user][hotel].get('relationship_type') == 'STAYED_AT':
                        user_ratings[hotel] = G[user][hotel].get('rating', 0)
            
            common_hotels = set(user_ratings.keys()) & set(user_hotel_ratings.keys())
            if common_hotels:
                ratings_similarity = sum(abs(user_ratings[h] - user_hotel_ratings[h]) 
                                      for h in common_hotels) / len(common_hotels)
                similarity_score += ratings_similarity
            
            # Experience preferences similarity
            user_likes = set()
            for exp in G.neighbors(user):
                if G.nodes[exp].get('type') == 'Experience':
                    if G[user][exp].get('relationship_type') == 'LIKES':
                        user_likes.add(exp)
            
            common_experiences = len(user_likes & user_liked_experiences)
            if common_experiences:
                similarity_score += common_experiences * 0.5
            
            if similarity_score > 0:
                similar_users.append((user, similarity_score))
    
    if not similar_users:
        return 0
    
    similar_users.sort(key=lambda x: x[1], reverse=True)
    similar_users = similar_users[:5]  # Top 5 most similar users
    
    weighted_score = 0
    total_weight = 0
    
    for user, similarity in similar_users:
        if G.has_edge(user, hotel_node):
            if G[user][hotel_node].get('relationship_type') == 'STAYED_AT':
                rating = G[user][hotel_node].get('rating', 0)
                weighted_score += rating * similarity
                total_weight += similarity
    
    return weighted_score / total_weight if total_weight > 0 else 0

def recommend_hotels_for_experiences(G, experience_preferences, user_email=None):
    """
    experience_preferences: [(experience_id, importance_score), ...]
    importance_score: importance score given by customer to this experience (1-5)
    user_email: User's email for personalization
    """
    experience_nodes = []
    for exp_id, _ in experience_preferences:
        for node in G.nodes():
            if (G.nodes[node].get('type') == 'Experience' and 
                G.nodes[node].get('experience_id') == exp_id):
                experience_nodes.append(node)
                break
    
    if not experience_nodes:
        return "Experiences not found"

    pagerank_scores = calculate_weighted_pagerank(G)
    user_hotel_ratings, user_liked_experiences = get_user_history(G, user_email) if user_email else (None, None)
    
    hotels_data = []
    for node in G.nodes():
        if G.nodes[node].get('type') == 'Hotel':
            if any(G.has_edge(node, exp_node) for exp_node in experience_nodes):
                collaborative_score = calculate_collaborative_score(G, node, user_hotel_ratings, user_liked_experiences)
                
                hotel_data = {
                    'node_id': node,
                    'name': G.nodes[node].get('name'),
                    'hotel_rating': G.nodes[node].get('rating', 0),
                    'pagerank_score': pagerank_scores[node],
                    'collaborative_score': collaborative_score,
                    'experience_count': 0,
                    'avg_experience_rating': 0.0,
                    'selected_experiences_ratings': []
                }
                
                total_rating = 0
                num_selected_experiences = 0
                
                for exp_node in experience_nodes:
                    if G.has_edge(node, exp_node):
                        exp_rating = G[node][exp_node].get('rating', 0)
                        exp_importance = next(score for id, score in experience_preferences 
                                           if G.nodes[exp_node].get('experience_id') == id)
                        hotel_data['selected_experiences_ratings'].append(
                            (exp_rating, exp_importance)
                        )
                        total_rating += exp_rating
                        num_selected_experiences += 1
                
                if num_selected_experiences > 0:
                    hotel_data['experience_count'] = num_selected_experiences
                    hotel_data['avg_experience_rating'] = total_rating / num_selected_experiences
                    
                    # Calculate final score
                    selected_exp_score = 0
                    if hotel_data['selected_experiences_ratings']:
                        weighted_ratings = [rating * (importance/5) 
                                         for rating, importance in hotel_data['selected_experiences_ratings']]
                        selected_exp_score = sum(weighted_ratings) / len(weighted_ratings)
                    
                    normalized_pagerank = (hotel_data['pagerank_score'] / max(pagerank_scores.values())) * 10
                    
                    hotel_data['final_score'] = (
                        hotel_data['avg_experience_rating'] * 0.25 +
                        selected_exp_score * 0.35 +
                        normalized_pagerank * 0.15 +
                        hotel_data['hotel_rating'] * 0.1 +
                        hotel_data['collaborative_score'] * 0.15
                    )
                    
                    hotels_data.append(hotel_data)
    
    # Sort by final score
    sorted_hotels = sorted(hotels_data, key=lambda x: x['final_score'], reverse=True)
    return sorted_hotels

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)