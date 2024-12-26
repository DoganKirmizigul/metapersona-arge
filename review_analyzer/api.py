from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import networkx as nx
import pandas as pd
import numpy as np
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Hotel Recommendation API", 
    description="Provides hotel recommendations based on experience preferences, location and user email",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExperiencePreference(BaseModel):
    experience_id: int
    importance: int

class RecommendationRequest(BaseModel):
    user_email: str
    location_id: int
    experience_preferences: List[ExperiencePreference]

class Experience(BaseModel):
    name: str
    rating: float

class HotelRecommendation(BaseModel):
    name: str
    hotel_rating: float
    selected_experiences_ratings: List[Tuple[float, int]]
    experience_count: int
    avg_experience_rating: float
    other_experiences: List[Experience] = []
    is_in_location: bool = False

class RecommendationResponse(BaseModel):
    recommendations: List[HotelRecommendation]

class HotelRecommender:
    def __init__(self):
        self.G = None
        self.experience_mapping = {
            1: "Water Slide",
            2: "Service Quality", 
            3: "Hygienic Holiday",
        }
        self._initialize_graph()

    def _initialize_graph(self):
        self.G = nx.Graph()
        
        self._load_nodes()
        self._load_edges()

    def _load_nodes(self):
        try:
            hotel_df = pd.read_csv('../graph_nodes_edges/hotel_nodes.csv', encoding='latin1')
            for _, row in hotel_df.iterrows():
                self.G.add_node(row['id'], 
                              type='Hotel', 
                              name=row['name'], 
                              rating=row['rating'],
                              hotel_id=row['id'])

            exp_df = pd.read_csv('../graph_nodes_edges/experience_nodes.csv', encoding='latin1')
            for _, row in exp_df.iterrows():
                self.G.add_node(row['id'],
                              type='Experience',
                              name=row['name'],
                              experience_id=row['experience_id'])

            user_df = pd.read_csv('../graph_nodes_edges/user_nodes.csv', encoding='latin1')
            for _, row in user_df.iterrows():
                self.G.add_node(row['id'],
                              type='User',
                              name=row['name'],
                              email=row['email'])

            location_df = pd.read_csv('../graph_nodes_edges/location_nodes.csv', encoding='latin1')
            for _, row in location_df.iterrows():
                self.G.add_node(row['id'],
                              type='Location',
                              name=row['name'])

        except Exception as e:
            raise Exception(f"Error loading nodes: {str(e)}")

    def _load_edges(self):
        try:
            exp_edges_df = pd.read_csv('../graph_nodes_edges/has_experience_edges.csv')
            for _, row in exp_edges_df.iterrows():
                self.G.add_edge(row['source'], row['target'],
                              relationship_type='HAS_EXPERIENCE',
                              rating=row['rating'])

            stayed_df = pd.read_csv('../graph_nodes_edges/stayed_at_edges.csv')
            for _, row in stayed_df.iterrows():
                self.G.add_edge(row['source'], row['target'],
                              relationship_type='STAYED_AT',
                              rating=row['rating'])

            likes_df = pd.read_csv('../graph_nodes_edges/likes_edges.csv')
            for _, row in likes_df.iterrows():
                self.G.add_edge(row['source'], row['target'],
                              relationship_type='LIKES')

            located_in_df = pd.read_csv('../graph_nodes_edges/located_in_edges.csv')
            for _, row in located_in_df.iterrows():
                self.G.add_edge(row['source'], row['target'],
                              relationship_type='LOCATED_IN')

        except Exception as e:
            raise Exception(f"Error loading edges: {str(e)}")

    def get_hotels_in_location(self, location_id: int) -> set:
        hotels_in_location = set()
        for node in self.G.nodes():
            if (self.G.nodes[node].get('type') == 'Hotel' and
                any(neighbor == location_id and 
                    self.G.edges[node, neighbor].get('relationship_type') == 'LOCATED_IN'
                    for neighbor in self.G.neighbors(node))):
                hotels_in_location.add(node)
        return hotels_in_location

    # ... [previous methods remain unchanged until recommend_hotels] ...

    def recommend_hotels(self, user_email: str, location_id: int, experience_preferences: List[ExperiencePreference]) -> List[HotelRecommendation]:
        try:
            hotels_in_location = self.get_hotels_in_location(location_id)
            
            experience_nodes = []
            formatted_preferences = [(pref.experience_id, pref.importance) 
                                  for pref in experience_preferences]
            
            for exp_id, _ in formatted_preferences:
                for node in self.G.nodes():
                    if (self.G.nodes[node].get('type') == 'Experience' and 
                        self.G.nodes[node].get('experience_id') == exp_id):
                        experience_nodes.append(node)
                        break

            if not experience_nodes:
                raise Exception("Experiences not found")

            pagerank_scores = self.calculate_weighted_pagerank(self.G)
            
            user_hotel_ratings, user_liked_experiences = self.get_user_history_weights(user_email)
            
            hotels_data = []
            for node in self.G.nodes():
                if self.G.nodes[node].get('type') == 'Hotel':
                    if any(self.G.has_edge(node, exp_node) for exp_node in experience_nodes):
                        collaborative_score = self.calculate_collaborative_score(node, user_email)
                        
                        hotel_data = {
                            'node_id': node,
                            'name': self.G.nodes[node].get('name'),
                            'hotel_rating': self.G.nodes[node].get('rating', 0),
                            'pagerank_score': pagerank_scores[node],
                            'collaborative_score': collaborative_score,
                            'experiences': [],
                            'experience_count': 0,
                            'avg_experience_rating': 0.0,
                            'selected_experiences_ratings': [],
                            'other_experiences': [],
                            'is_in_location': node in hotels_in_location
                        }
                        
                        total_rating = 0
                        num_experiences = 0
                        
                        # Otel deneyimlerini işle
                        for exp_node in self.G.neighbors(node):
                            if self.G.nodes[exp_node].get('type') == 'Experience':
                                edge_data = self.G.edges[node, exp_node]
                                if edge_data.get('relationship_type') == 'HAS_EXPERIENCE':
                                    exp_rating = edge_data.get('rating', 0)
                                    exp_id = self.G.nodes[exp_node].get('experience_id')
                                    
                                    # Seçilen deneyimler için puanları kaydet
                                    for pref_id, importance in formatted_preferences:
                                        if exp_id == pref_id:
                                            hotel_data['selected_experiences_ratings'].append(
                                                (exp_rating, importance)
                                            )
                                            break
                                    else:
                                        # Seçilmeyen deneyimleri diğer deneyimler listesine ekle
                                        hotel_data['other_experiences'].append(Experience(
                                            name=self.G.nodes[exp_node].get('name'),
                                            rating=exp_rating
                                        ))
                                    
                                    total_rating += exp_rating
                                    num_experiences += 1
                        
                        if num_experiences > 0:
                            hotel_data['experience_count'] = num_experiences
                            hotel_data['avg_experience_rating'] = total_rating / num_experiences
                            hotels_data.append(hotel_data)

            def calculate_score(hotel):
                location_bonus = 2.0 if hotel['is_in_location'] else 0.0
                
                selected_exp_score = 0
                if hotel['selected_experiences_ratings']:
                    weighted_ratings = [rating * (importance/5) 
                                      for rating, importance in hotel['selected_experiences_ratings']]
                    selected_exp_score = sum(weighted_ratings) / len(weighted_ratings)
                
                base_score = (
                    hotel['avg_experience_rating'] * 0.25 +
                    selected_exp_score * 0.35 +
                    hotel['pagerank_score'] * 0.15 +
                    hotel['hotel_rating'] * 0.1 +
                    hotel['collaborative_score'] * 0.15
                )
                
                history_score = 0
                if user_email and user_hotel_ratings is not None:
                    history_similarity = self.calculate_history_similarity(
                        hotel['node_id'],
                        user_hotel_ratings,
                        user_liked_experiences
                    )
                    history_score = history_similarity * 0.3
                    
                final_score = (base_score * 0.7 + history_score) + location_bonus
                
                return final_score

            sorted_hotels = sorted(hotels_data, key=calculate_score, reverse=True)
            
            recommendations = []
            for hotel in sorted_hotels[:5]:
                recommendations.append(HotelRecommendation(
                    name=hotel['name'],
                    hotel_rating=hotel['hotel_rating'],
                    selected_experiences_ratings=hotel['selected_experiences_ratings'],
                    experience_count=hotel['experience_count'],
                    avg_experience_rating=hotel['avg_experience_rating'],
                    other_experiences=hotel['other_experiences'],
                    is_in_location=hotel['is_in_location']
                ))
                
            return recommendations

        except Exception as e:
            raise Exception(f"Error calculating recommendations: {str(e)}")

    def calculate_weighted_pagerank(self, G):
        # Düğüm ağırlıklarını hazırla
        weights = {}
        for node in G.nodes():
            if G.nodes[node].get('type') == 'Hotel':
                weights[node] = G.nodes[node].get('rating', 0.5)
            elif G.nodes[node].get('type') == 'Experience':
                connected_hotels = [n for n in G.neighbors(node) 
                                 if G.nodes[n].get('type') == 'Hotel']
                if connected_hotels:
                    avg_rating = np.mean([G.nodes[h].get('rating', 0.5) 
                                       for h in connected_hotels])
                    weights[node] = avg_rating
                else:
                    weights[node] = 0.5
            else:
                weights[node] = 0.5
        
        try:
            # PageRank hesapla - daha yüksek max_iter ve daha düşük tol değerleri ile
            return nx.pagerank(
                G,
                personalization=weights,
                max_iter=1000,  # İterasyon sayısını artır
                tol=1e-6,      # Toleransı düşür
                alpha=0.85     # Sönümleme faktörü
            )
        except:
            # Yakınsama başarısız olursa, basit bir sıralama döndür
            simple_ranks = {}
            for node in G.nodes():
                simple_ranks[node] = weights.get(node, 0.5)
            return simple_ranks

    def get_user_history_weights(self, user_email: str) -> Tuple[dict, set]:
        try:
            # Kullanıcı düğümünü bul
            user_node = None
            for node in self.G.nodes():
                if (self.G.nodes[node].get('type') == 'User' and 
                    self.G.nodes[node].get('email') == user_email):
                    user_node = node
                    break
            
            if not user_node:
                return None, None
            
            # Kullanıcının otel değerlendirmelerini topla
            hotel_ratings = {}
            for neighbor in self.G.neighbors(user_node):
                if self.G.nodes[neighbor].get('type') == 'Hotel':
                    edge_data = self.G.edges[user_node, neighbor]
                    if edge_data.get('relationship_type') == 'STAYED_AT':
                        hotel_ratings[neighbor] = edge_data.get('rating', 0)
            
            # Kullanıcının beğendiği deneyimleri topla
            liked_experiences = set()
            for neighbor in self.G.neighbors(user_node):
                if (self.G.nodes[neighbor].get('type') == 'Experience' and 
                    self.G.edges[user_node, neighbor].get('relationship_type') == 'LIKES'):
                    liked_experiences.add(neighbor)
            
            return hotel_ratings, liked_experiences
            
        except Exception as e:
            print(f"Error getting user history: {str(e)}")
            return None, None

    def calculate_collaborative_score(self, hotel_node: int, user_email: str) -> float:
        try:
            # Kullanıcı düğümünü bul
            user_node = None
            for node in self.G.nodes():
                if (self.G.nodes[node].get('type') == 'User' and 
                    self.G.nodes[node].get('email') == user_email):
                    user_node = node
                    break
            
            if not user_node:
                return 0.0
            
            # Bu otelde kalan diğer kullanıcıları bul
            similar_users = []
            hotel_ratings = []
            
            for node in self.G.nodes():
                if self.G.nodes[node].get('type') == 'User' and node != user_node:
                    if self.G.has_edge(node, hotel_node):
                        edge_data = self.G.edges[node, hotel_node]
                        if edge_data.get('relationship_type') == 'STAYED_AT':
                            similar_users.append(node)
                            hotel_ratings.append(edge_data.get('rating', 0))
            
            if not similar_users:
                return self.G.nodes[hotel_node].get('rating', 0) * 0.5
            
            # Benzer kullanıcıların ortalama puanını hesapla
            avg_rating = np.mean(hotel_ratings)
            
            # Benzerlik ağırlığını hesapla (0.5 ile 1.0 arasında)
            similarity_weight = min(len(similar_users) / 10, 1.0) * 0.5 + 0.5
            
            return avg_rating * similarity_weight
            
        except Exception as e:
            print(f"Error calculating collaborative score: {str(e)}")
            return 0.0

    def calculate_history_similarity(self, hotel_node: int, user_hotel_ratings: dict, user_liked_experiences: set) -> float:
        try:
            if not user_hotel_ratings and not user_liked_experiences:
                return 0.0
            
            similarity_score = 0.0
            total_weight = 0.0
            
            # Otel puanlarına dayalı benzerlik
            if user_hotel_ratings:
                # Otelin deneyimlerini al
                hotel_experiences = set()
                for neighbor in self.G.neighbors(hotel_node):
                    if self.G.nodes[neighbor].get('type') == 'Experience':
                        hotel_experiences.add(neighbor)
                
                # Kullanıcının daha önce kaldığı otellerin deneyimlerini karşılaştır
                for rated_hotel, rating in user_hotel_ratings.items():
                    rated_hotel_experiences = set()
                    for neighbor in self.G.neighbors(rated_hotel):
                        if self.G.nodes[neighbor].get('type') == 'Experience':
                            rated_hotel_experiences.add(neighbor)
                    
                    # Jaccard benzerliği hesapla
                    common_experiences = len(hotel_experiences.intersection(rated_hotel_experiences))
                    total_experiences = len(hotel_experiences.union(rated_hotel_experiences))
                    
                    if total_experiences > 0:
                        experience_similarity = common_experiences / total_experiences
                        # Kullanıcının verdiği puana göre ağırlıklandır
                        similarity_score += experience_similarity * (rating / 5.0)
                        total_weight += 1
            
            # Beğenilen deneyimlere dayalı benzerlik
            if user_liked_experiences:
                hotel_experiences = set()
                for neighbor in self.G.neighbors(hotel_node):
                    if self.G.nodes[neighbor].get('type') == 'Experience':
                        hotel_experiences.add(neighbor)
                
                common_liked = len(hotel_experiences.intersection(user_liked_experiences))
                if common_liked > 0:
                    liked_similarity = common_liked / len(user_liked_experiences)
                    similarity_score += liked_similarity
                    total_weight += 1
            
            # Ağırlıklı ortalama hesapla
            if total_weight > 0:
                return similarity_score / total_weight
            return 0.0
            
        except Exception as e:
            print(f"Error calculating history similarity: {str(e)}")
            return 0.0

recommender = HotelRecommender()

@app.post("/recommend/", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    try:
        recommendations = recommender.recommend_hotels(
            request.user_email,
            request.location_id,
            request.experience_preferences
        )
        return RecommendationResponse(recommendations=recommendations)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/experiences/")
async def get_experiences():
    return recommender.experience_mapping

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)