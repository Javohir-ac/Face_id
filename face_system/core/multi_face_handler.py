"""
Multi-Face Handler - Advanced handling of multiple faces in frame
"""
import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
import threading
from .error_handler import get_error_handler, handle_errors

class FaceTracker:
    """Track individual face across frames"""
    
    def __init__(self, face_id: str, initial_location: Tuple[int, int, int, int], 
                 initial_encoding: np.ndarray, confidence: float):
        self.face_id = face_id
        self.locations = [initial_location]
        self.encodings = [initial_encoding]
        self.confidences = [confidence]
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
        self.recognition_count = 1
        self.is_stable = False
        self.predicted_name = "Unknown"
        self.name_confidence = 0.0
    
    def update(self, location: Tuple[int, int, int, int], encoding: np.ndarray, 
               confidence: float, predicted_name: str, name_confidence: float):
        """Update tracker with new detection"""
        self.locations.append(location)
        self.encodings.append(encoding)
        self.confidences.append(confidence)
        self.last_seen = datetime.now()
        self.recognition_count += 1
        
        # Update predicted name if confidence is higher
        if name_confidence > self.name_confidence:
            self.predicted_name = predicted_name
            self.name_confidence = name_confidence
        
        # Consider stable after 3 consistent detections
        if self.recognition_count >= 3 and not self.is_stable:
            self.is_stable = True
        
        # Keep only last 10 detections for memory efficiency
        if len(self.locations) > 10:
            self.locations = self.locations[-10:]
            self.encodings = self.encodings[-10:]
            self.confidences = self.confidences[-10:]
    
    def get_average_location(self) -> Tuple[int, int, int, int]:
        """Get average face location"""
        if not self.locations:
            return (0, 0, 0, 0)
        
        avg_top = sum(loc[0] for loc in self.locations) // len(self.locations)
        avg_right = sum(loc[1] for loc in self.locations) // len(self.locations)
        avg_bottom = sum(loc[2] for loc in self.locations) // len(self.locations)
        avg_left = sum(loc[3] for loc in self.locations) // len(self.locations)
        
        return (avg_top, avg_right, avg_bottom, avg_left)
    
    def get_movement_vector(self) -> Tuple[float, float]:
        """Get face movement direction"""
        if len(self.locations) < 2:
            return (0.0, 0.0)
        
        first_loc = self.locations[0]
        last_loc = self.locations[-1]
        
        # Calculate center points
        first_center = ((first_loc[3] + first_loc[1]) / 2, (first_loc[0] + first_loc[2]) / 2)
        last_center = ((last_loc[3] + last_loc[1]) / 2, (last_loc[0] + last_loc[2]) / 2)
        
        # Movement vector
        dx = last_center[0] - first_center[0]
        dy = last_center[1] - first_center[1]
        
        return (dx, dy)
    
    def is_expired(self, timeout_seconds: int = 5) -> bool:
        """Check if tracker has expired"""
        return (datetime.now() - self.last_seen).total_seconds() > timeout_seconds

class MultiFaceHandler:
    """Advanced multi-face detection and tracking"""
    
    def __init__(self, face_system):
        self.face_system = face_system
        self.error_handler = get_error_handler()
        
        # Face tracking
        self.active_trackers: Dict[str, FaceTracker] = {}
        self.next_face_id = 1
        self.lock = threading.Lock()
        
        # Configuration
        self.max_face_distance = 100  # pixels
        self.tracker_timeout = 5  # seconds
        self.min_face_size = 50  # pixels
        self.max_faces_per_frame = 10
        
        # Statistics
        self.stats = {
            'total_faces_detected': 0,
            'simultaneous_faces_max': 0,
            'tracking_sessions': 0,
            'recognition_attempts': 0,
            'successful_recognitions': 0
        }
        
        print("👥 MultiFaceHandler initialized")
    
    @handle_errors("Multi-Face Processing")
    def process_faces(self, face_locations: List[Tuple[int, int, int, int]], 
                     face_encodings: List[np.ndarray]) -> List[Dict]:
        """Process multiple faces in frame"""
        with self.lock:
            processed_faces = []
            current_time = datetime.now()
            
            # Clean up expired trackers
            self._cleanup_expired_trackers()
            
            # Limit number of faces to process
            if len(face_locations) > self.max_faces_per_frame:
                # Sort by face size (larger faces first)
                face_data = list(zip(face_locations, face_encodings))
                face_data.sort(key=lambda x: self._calculate_face_size(x[0]), reverse=True)
                face_locations = [x[0] for x in face_data[:self.max_faces_per_frame]]
                face_encodings = [x[1] for x in face_data[:self.max_faces_per_frame]]
            
            # Update statistics
            self.stats['total_faces_detected'] += len(face_locations)
            self.stats['simultaneous_faces_max'] = max(
                self.stats['simultaneous_faces_max'], 
                len(face_locations)
            )
            
            # Process each detected face
            for location, encoding in zip(face_locations, face_encodings):
                try:
                    # Skip small faces
                    if self._calculate_face_size(location) < self.min_face_size:
                        continue
                    
                    # Find matching tracker or create new one
                    tracker = self._find_or_create_tracker(location, encoding)
                    
                    # Recognize face
                    self.stats['recognition_attempts'] += 1
                    name, confidence = self.face_system.recognize_face(encoding)
                    
                    if name != "Unknown":
                        self.stats['successful_recognitions'] += 1
                    
                    # Update tracker
                    tracker.update(location, encoding, confidence, name, confidence)
                    
                    # Prepare face data
                    face_data = {
                        'face_id': tracker.face_id,
                        'location': location,
                        'name': name,
                        'confidence': confidence,
                        'is_stable': tracker.is_stable,
                        'recognition_count': tracker.recognition_count,
                        'movement_vector': tracker.get_movement_vector(),
                        'duration': (current_time - tracker.first_seen).total_seconds(),
                        'priority': self._calculate_face_priority(tracker, name, confidence)
                    }
                    
                    processed_faces.append(face_data)
                    
                except Exception as e:
                    self.error_handler.log_error(e, "Individual face processing")
            
            # Sort faces by priority (highest first)
            processed_faces.sort(key=lambda x: x['priority'], reverse=True)
            
            return processed_faces
    
    def _find_or_create_tracker(self, location: Tuple[int, int, int, int], 
                               encoding: np.ndarray) -> FaceTracker:
        """Find existing tracker or create new one"""
        # Try to match with existing trackers
        best_match = None
        min_distance = float('inf')
        
        for tracker in self.active_trackers.values():
            if not tracker.locations:
                continue
            
            # Calculate distance to last known location
            last_location = tracker.locations[-1]
            distance = self._calculate_location_distance(location, last_location)
            
            if distance < self.max_face_distance and distance < min_distance:
                min_distance = distance
                best_match = tracker
        
        if best_match:
            return best_match
        
        # Create new tracker
        face_id = f"face_{self.next_face_id}"
        self.next_face_id += 1
        
        tracker = FaceTracker(face_id, location, encoding, 0.0)
        self.active_trackers[face_id] = tracker
        self.stats['tracking_sessions'] += 1
        
        return tracker
    
    def _calculate_location_distance(self, loc1: Tuple[int, int, int, int], 
                                   loc2: Tuple[int, int, int, int]) -> float:
        """Calculate distance between two face locations"""
        # Calculate center points
        center1 = ((loc1[3] + loc1[1]) / 2, (loc1[0] + loc1[2]) / 2)
        center2 = ((loc2[3] + loc2[1]) / 2, (loc2[0] + loc2[2]) / 2)
        
        # Euclidean distance
        dx = center1[0] - center2[0]
        dy = center1[1] - center2[1]
        
        return np.sqrt(dx*dx + dy*dy)
    
    def _calculate_face_size(self, location: Tuple[int, int, int, int]) -> int:
        """Calculate face size in pixels"""
        top, right, bottom, left = location
        width = right - left
        height = bottom - top
        return width * height
    
    def _calculate_face_priority(self, tracker: FaceTracker, name: str, confidence: float) -> float:
        """Calculate face processing priority"""
        priority = 0.0
        
        # Higher priority for recognized faces
        if name != "Unknown":
            priority += confidence * 100
        
        # Higher priority for stable tracking
        if tracker.is_stable:
            priority += 50
        
        # Higher priority for longer tracking
        priority += min(tracker.recognition_count * 5, 25)
        
        # Higher priority for larger faces
        if tracker.locations:
            face_size = self._calculate_face_size(tracker.locations[-1])
            priority += min(face_size / 100, 25)
        
        return priority
    
    def _cleanup_expired_trackers(self):
        """Remove expired face trackers"""
        expired_trackers = []
        
        for face_id, tracker in self.active_trackers.items():
            if tracker.is_expired(self.tracker_timeout):
                expired_trackers.append(face_id)
        
        for face_id in expired_trackers:
            del self.active_trackers[face_id]
    
    def get_primary_face(self, processed_faces: List[Dict]) -> Optional[Dict]:
        """Get the primary face for action processing"""
        if not processed_faces:
            return None
        
        # Filter for recognized faces first
        recognized_faces = [face for face in processed_faces if face['name'] != "Unknown"]
        
        if recognized_faces:
            # Return highest priority recognized face
            return recognized_faces[0]
        
        # If no recognized faces, return highest priority unknown face
        return processed_faces[0]
    
    def get_zone_faces(self, processed_faces: List[Dict], frame_width: int) -> Dict[str, List[Dict]]:
        """Categorize faces by zones"""
        zones = {
            'entry': [],
            'neutral': [],
            'exit': []
        }
        
        for face in processed_faces:
            location = face['location']
            face_center_x = (location[3] + location[1]) / 2
            zone_ratio = face_center_x / frame_width
            
            if zone_ratio < 0.3:
                zones['entry'].append(face)
            elif zone_ratio > 0.7:
                zones['exit'].append(face)
            else:
                zones['neutral'].append(face)
        
        return zones
    
    def should_process_action(self, face_data: Dict, last_actions: Dict) -> bool:
        """Determine if face should trigger an action"""
        face_id = face_data['face_id']
        name = face_data['name']
        
        # Skip unknown faces
        if name == "Unknown":
            return False
        
        # Skip if not stable
        if not face_data['is_stable']:
            return False
        
        # Skip if confidence too low
        if face_data['confidence'] < 0.5:
            return False
        
        # Check cooldown
        current_time = datetime.now()
        last_action_time = last_actions.get(name)
        
        if last_action_time:
            time_diff = (current_time - last_action_time).total_seconds()
            if time_diff < 60:  # 1 minute cooldown
                return False
        
        return True
    
    def draw_face_info(self, frame: np.ndarray, processed_faces: List[Dict]):
        """Draw face tracking information on frame"""
        try:
            for face in processed_faces:
                location = face['location']
                top, right, bottom, left = location
                
                # Face rectangle color based on recognition
                if face['name'] != "Unknown":
                    color = (0, 255, 0)  # Green for recognized
                    if face['is_stable']:
                        color = (0, 255, 255)  # Yellow for stable recognized
                else:
                    color = (0, 0, 255)  # Red for unknown
                
                # Draw rectangle
                thickness = 3 if face['is_stable'] else 2
                cv2.rectangle(frame, (left, top), (right, bottom), color, thickness)
                
                # Face info text
                label = f"{face['name']} ({face['confidence']:.2f})"
                cv2.putText(frame, label, (left, top-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Face ID and tracking info
                info_text = f"ID:{face['face_id']} Count:{face['recognition_count']}"
                cv2.putText(frame, info_text, (left, bottom+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                
                # Priority indicator
                priority_text = f"P:{face['priority']:.0f}"
                cv2.putText(frame, priority_text, (right-50, top-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                
                # Movement vector
                movement = face['movement_vector']
                if abs(movement[0]) > 5 or abs(movement[1]) > 5:
                    center_x = (left + right) // 2
                    center_y = (top + bottom) // 2
                    end_x = int(center_x + movement[0] * 2)
                    end_y = int(center_y + movement[1] * 2)
                    cv2.arrowedLine(frame, (center_x, center_y), (end_x, end_y), 
                                   (255, 255, 0), 2)
        
        except Exception as e:
            self.error_handler.log_error(e, "Face info drawing")
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get face tracking statistics"""
        active_count = len(self.active_trackers)
        stable_count = sum(1 for t in self.active_trackers.values() if t.is_stable)
        recognized_count = sum(1 for t in self.active_trackers.values() 
                              if t.predicted_name != "Unknown")
        
        return {
            **self.stats,
            'active_trackers': active_count,
            'stable_trackers': stable_count,
            'recognized_trackers': recognized_count,
            'recognition_rate': (
                self.stats['successful_recognitions'] / 
                max(self.stats['recognition_attempts'], 1) * 100
            )
        }
    
    def print_tracking_stats(self):
        """Print face tracking statistics"""
        stats = self.get_tracking_stats()
        
        print(f"""
👥 Multi-Face Tracking Statistics:
   Total Faces Detected: {stats['total_faces_detected']}
   Max Simultaneous: {stats['simultaneous_faces_max']}
   Active Trackers: {stats['active_trackers']}
   Stable Trackers: {stats['stable_trackers']}
   Recognized Trackers: {stats['recognized_trackers']}
   Tracking Sessions: {stats['tracking_sessions']}
   Recognition Rate: {stats['recognition_rate']:.1f}%
        """)
    
    def reset_tracking(self):
        """Reset all face tracking"""
        with self.lock:
            self.active_trackers.clear()
            self.next_face_id = 1
            print("🔄 Face tracking reset")

# Global multi-face handler instance
_multi_face_handler = None

def get_multi_face_handler(face_system) -> MultiFaceHandler:
    """Get global multi-face handler instance"""
    global _multi_face_handler
    if _multi_face_handler is None:
        _multi_face_handler = MultiFaceHandler(face_system)
    return _multi_face_handler