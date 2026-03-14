"""
Fast Search Algorithm - Face Recognition System
"""
import numpy as np
from typing import List, Tuple, Optional, Dict
import time
from sklearn.neighbors import NearestNeighbors
import threading

class FastFaceSearch:
    """High-performance face search using optimized algorithms"""
    
    def __init__(self, algorithm='ball_tree', n_neighbors=5):
        self.algorithm = algorithm  # 'ball_tree', 'kd_tree', 'brute'
        self.n_neighbors = n_neighbors
        self.model = None
        self.encodings = None
        self.names = None
        self.is_trained = False
        self.lock = threading.RLock()
        
        print(f"🔍 FastFaceSearch initialized - Algorithm: {algorithm}")
    
    def train(self, encodings: List[np.ndarray], names: List[str]) -> bool:
        """Train the search model"""
        try:
            with self.lock:
                if len(encodings) == 0:
                    return False
                
                # Convert to numpy array for sklearn
                self.encodings = np.array(encodings)
                self.names = names
                
                # Choose optimal algorithm based on data size
                if len(encodings) < 50:
                    algorithm = 'brute'  # Fast for small datasets
                elif len(encodings) < 200:
                    algorithm = 'ball_tree'  # Good for medium datasets
                else:
                    algorithm = 'kd_tree'  # Best for large datasets
                
                # Initialize and train model
                self.model = NearestNeighbors(
                    n_neighbors=min(self.n_neighbors, len(encodings)),
                    algorithm=algorithm,
                    metric='euclidean',
                    n_jobs=-1  # Use all CPU cores
                )
                
                train_start = time.time()
                self.model.fit(self.encodings)
                train_time = time.time() - train_start
                
                self.is_trained = True
                print(f"⚡ Search model trained in {train_time:.3f}s - {len(encodings)} encodings, algorithm: {algorithm}")
                
                return True
                
        except Exception as e:
            print(f"❌ Search model training error: {e}")
            return False
    
    def search(self, query_encoding: np.ndarray, threshold: float = 0.55) -> Tuple[str, float]:
        """Fast search for best match"""
        if not self.is_trained or self.model is None:
            return "Unknown", 0.0
        
        try:
            with self.lock:
                # Reshape for sklearn
                query = query_encoding.reshape(1, -1)
                
                # Find nearest neighbors
                distances, indices = self.model.kneighbors(query)
                
                # Convert distances to face_recognition format (lower is better)
                distances = distances[0]  # Get first (and only) query result
                indices = indices[0]
                
                # Voting system with early exit
                votes = {}
                confidences = {}
                
                for i, (distance, idx) in enumerate(zip(distances, indices)):
                    if distance > threshold:
                        continue  # Skip if too far
                    
                    name = self.names[idx]
                    confidence = 1.0 - distance
                    
                    if name not in votes:
                        votes[name] = 0
                        confidences[name] = []
                    
                    votes[name] += 1
                    confidences[name].append(confidence)
                    
                    # Early exit if we have strong confidence
                    if votes[name] >= 3 and confidence > 0.8:
                        avg_confidence = np.mean(confidences[name])
                        return name, avg_confidence
                
                # No early exit, find best match
                if not votes:
                    return "Unknown", 1.0 - distances[0] if len(distances) > 0 else 0.0
                
                # Handle tie situation - choose by highest confidence
                max_votes = max(votes.values())
                tied_candidates = [name for name, vote_count in votes.items() if vote_count == max_votes]
                
                if len(tied_candidates) == 1:
                    # Clear winner
                    best_name = tied_candidates[0]
                    avg_confidence = np.mean(confidences[best_name])
                else:
                    # TIE situation - choose by highest average confidence
                    best_name = max(tied_candidates, key=lambda name: np.mean(confidences[name]))
                    avg_confidence = np.mean(confidences[best_name])
                    print(f"🤝 TIE resolved: {tied_candidates} -> {best_name} (confidence: {avg_confidence:.3f})")
                
                # Minimum requirements
                if votes[best_name] >= 2 and avg_confidence >= 0.5:
                    return best_name, avg_confidence
                else:
                    return "Unknown", avg_confidence
                    
        except Exception as e:
            print(f"❌ Fast search error: {e}")
            return "Unknown", 0.0
    
    def batch_search(self, query_encodings: List[np.ndarray], threshold: float = 0.55) -> List[Tuple[str, float]]:
        """Batch search for multiple queries"""
        if not self.is_trained or self.model is None:
            return [("Unknown", 0.0)] * len(query_encodings)
        
        try:
            with self.lock:
                # Convert to numpy array
                queries = np.array(query_encodings)
                
                # Batch nearest neighbors search
                distances, indices = self.model.kneighbors(queries)
                
                results = []
                for i in range(len(query_encodings)):
                    query_distances = distances[i]
                    query_indices = indices[i]
                    
                    # Voting for this query
                    votes = {}
                    confidences = {}
                    
                    for distance, idx in zip(query_distances, query_indices):
                        if distance > threshold:
                            continue
                        
                        name = self.names[idx]
                        confidence = 1.0 - distance
                        
                        if name not in votes:
                            votes[name] = 0
                            confidences[name] = []
                        
                        votes[name] += 1
                        confidences[name].append(confidence)
                    
                    # Determine result
                    if not votes:
                        results.append(("Unknown", 1.0 - query_distances[0] if len(query_distances) > 0 else 0.0))
                    else:
                        best_name = max(votes.keys(), key=lambda x: votes[x])
                        avg_confidence = np.mean(confidences[best_name])
                        
                        if votes[best_name] >= 2 and avg_confidence >= 0.5:
                            results.append((best_name, avg_confidence))
                        else:
                            results.append(("Unknown", avg_confidence))
                
                return results
                
        except Exception as e:
            print(f"❌ Batch search error: {e}")
            return [("Unknown", 0.0)] * len(query_encodings)
    
    def get_stats(self) -> Dict:
        """Get search statistics"""
        return {
            'is_trained': self.is_trained,
            'algorithm': self.algorithm,
            'n_encodings': len(self.encodings) if self.encodings is not None else 0,
            'n_neighbors': self.n_neighbors,
            'model_type': type(self.model).__name__ if self.model else None
        }

# Global fast search instance
_fast_search = None

def get_fast_search() -> FastFaceSearch:
    """Get global fast search instance"""
    global _fast_search
    if _fast_search is None:
        _fast_search = FastFaceSearch()
    return _fast_search