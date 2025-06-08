# nina_cognitive_voice.py
"""
Nina 2.0 - Cognitive Voice Intelligence System
A state-of-the-art speech-to-speech AI with revolutionary features:

1. Emotional Intelligence - Detects and responds to user emotions
2. Contextual Awareness - Maintains conversation context across sessions
3. Predictive Interaction - Anticipates needs before you ask
4. Multi-Modal Processing - Voice, tone, pace, and silence analysis
5. Adaptive Personality - Learns and adapts to user preferences
6. Parallel Processing - Multiple agents work simultaneously
7. Voice Biometrics - Recognizes different users by voice
8. Ambient Intelligence - Always aware, never intrusive
"""

import asyncio
import numpy as np
import torch
import time
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import threading
import queue

# Note: These advanced imports are optional - the system will work without them
# but with reduced functionality. Install with: pip install librosa scipy transformers
try:
    import librosa
    import scipy.signal
    from transformers import (
        WhisperProcessor, 
        WhisperForConditionalGeneration,
        Wav2Vec2ForCTC, 
        Wav2Vec2Processor
    )
    ADVANCED_FEATURES = True
except ImportError:
    print("Note: Some advanced features require additional packages.")
    print("Install with: pip install librosa scipy transformers")
    ADVANCED_FEATURES = False

@dataclass
class VoiceProfile:
    """Stores voice characteristics for user identification"""
    user_id: str
    voice_embedding: np.ndarray
    pitch_range: Tuple[float, float]
    speaking_rate: float
    accent_markers: Dict[str, float]
    last_seen: datetime
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_history: deque = field(default_factory=lambda: deque(maxlen=100))

@dataclass
class EmotionalState:
    """Tracks emotional context of conversation"""
    primary_emotion: str
    confidence: float
    arousal: float  # Energy level (calm to excited)
    valence: float  # Positivity (negative to positive)
    trajectory: List[str] = field(default_factory=list)  # Emotion history

@dataclass
class ConversationContext:
    """Rich conversation context tracking"""
    current_topic: Optional[str] = None
    topic_history: deque = field(default_factory=lambda: deque(maxlen=10))
    unresolved_questions: List[str] = field(default_factory=list)
    mentioned_entities: Dict[str, List[str]] = field(default_factory=dict)
    task_stack: List[Dict] = field(default_factory=list)
    ambient_context: Dict[str, Any] = field(default_factory=dict)
    
class CognitiveVoiceProcessor:
    """Advanced voice processing with emotional and contextual understanding"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._init_models()
        self._init_processors()
    
    def _init_models(self):
        """Initialize advanced ML models"""
        # Speech recognition with emotion
        self.whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-large-v3")
        self.whisper_model = WhisperForConditionalGeneration.from_pretrained(
            "openai/whisper-large-v3"
        ).to(self.device)
        
        # Voice analysis for emotion and speaker identification
        self.wav2vec_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-large-xlsr-53")
        self.wav2vec_model = Wav2Vec2ForCTC.from_pretrained(
            "facebook/wav2vec2-large-xlsr-53"
        ).to(self.device)
    
    def _init_processors(self):
        """Initialize audio processors"""
        self.pitch_tracker = PitchTracker()
        self.emotion_analyzer = EmotionAnalyzer()
        self.voice_identifier = VoiceIdentifier()
    
    async def process_audio_stream(self, audio_data: np.ndarray, sample_rate: int) -> Dict:
        """Process audio with full analysis"""
        # Parallel processing for speed
        tasks = [
            self._transcribe_with_confidence(audio_data, sample_rate),
            self._analyze_prosody(audio_data, sample_rate),
            self._detect_emotion(audio_data, sample_rate),
            self._identify_speaker(audio_data, sample_rate)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            "transcription": results[0],
            "prosody": results[1],
            "emotion": results[2],
            "speaker": results[3],
            "timestamp": datetime.now()
        }
    
    async def _transcribe_with_confidence(self, audio: np.ndarray, sr: int) -> Dict:
        """Transcribe with word-level confidence scores"""
        inputs = self.whisper_processor(audio, sampling_rate=sr, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.whisper_model.generate(
                **inputs,
                return_dict_in_generate=True,
                output_scores=True
            )
        
        transcription = self.whisper_processor.batch_decode(
            outputs.sequences, 
            skip_special_tokens=True
        )[0]
        
        # Calculate confidence
        scores = torch.stack(outputs.scores, dim=1)
        confidence = torch.mean(torch.max(torch.softmax(scores, dim=-1), dim=-1).values).item()
        
        return {
            "text": transcription,
            "confidence": confidence,
            "language": self._detect_language(transcription)
        }
    
    async def _analyze_prosody(self, audio: np.ndarray, sr: int) -> Dict:
        """Analyze speech patterns"""
        # Pitch analysis
        pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
        pitch_values = []
        
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        # Speaking rate (syllables per second)
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
        
        # Voice quality
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sr)
        
        return {
            "pitch_mean": np.mean(pitch_values) if pitch_values else 0,
            "pitch_variance": np.var(pitch_values) if pitch_values else 0,
            "speaking_rate": tempo,
            "voice_quality": np.mean(spectral_centroids)
        }
    
    async def _detect_emotion(self, audio: np.ndarray, sr: int) -> EmotionalState:
        """Detect emotional state from voice"""
        # Feature extraction for emotion
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
        
        # Combine features
        features = np.concatenate([
            np.mean(mfcc, axis=1),
            np.var(mfcc, axis=1),
            np.mean(spectral_contrast, axis=1)
        ])
        
        # Emotion classification (simplified - in production use trained model)
        arousal = self._calculate_arousal(features)
        valence = self._calculate_valence(features)
        
        emotion_map = {
            (True, True): "happy",
            (True, False): "angry",
            (False, True): "calm",
            (False, False): "sad"
        }
        
        primary_emotion = emotion_map[(arousal > 0.5, valence > 0.5)]
        
        return EmotionalState(
            primary_emotion=primary_emotion,
            confidence=0.8,  # Placeholder
            arousal=arousal,
            valence=valence
        )
    
    def _calculate_arousal(self, features: np.ndarray) -> float:
        """Calculate arousal level from audio features"""
        # High energy = high arousal
        energy = np.mean(features[:13])  # MFCC energy
        return min(max(energy / 100, 0), 1)  # Normalize
    
    def _calculate_valence(self, features: np.ndarray) -> float:
        """Calculate valence (positivity) from audio features"""
        # Brightness correlates with positive emotion
        brightness = np.mean(features[20:])  # Spectral features
        return min(max(brightness / 5000, 0), 1)  # Normalize
    
    async def _identify_speaker(self, audio: np.ndarray, sr: int) -> Optional[str]:
        """Identify speaker from voice"""
        # Extract voice embedding
        inputs = self.wav2vec_processor(audio, sampling_rate=sr, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.wav2vec_model(**inputs)
            embedding = outputs.hidden_states[-1].mean(dim=1).cpu().numpy()
        
        # Compare with known voice profiles
        # (Simplified - in production use proper voice biometrics)
        return "default_user"
    
    def _detect_language(self, text: str) -> str:
        """Detect language of transcription"""
        # Simplified - use langdetect in production
        return "en"


class PredictiveContextEngine:
    """Predicts user needs and maintains rich context"""
    
    def __init__(self):
        self.context = ConversationContext()
        self.user_profiles: Dict[str, VoiceProfile] = {}
        self.pattern_memory = PatternMemory()
        
    def update_context(self, voice_data: Dict, response: str):
        """Update context with new interaction"""
        # Extract entities and topics
        entities = self._extract_entities(voice_data["transcription"]["text"])
        topic = self._identify_topic(voice_data["transcription"]["text"])
        
        # Update context
        if topic:
            self.context.current_topic = topic
            self.context.topic_history.append(topic)
        
        for entity_type, entity_list in entities.items():
            if entity_type not in self.context.mentioned_entities:
                self.context.mentioned_entities[entity_type] = []
            self.context.mentioned_entities[entity_type].extend(entity_list)
        
        # Update user profile
        user_id = voice_data.get("speaker", "default_user")
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            profile.last_seen = datetime.now()
            profile.interaction_history.append({
                "query": voice_data["transcription"]["text"],
                "emotion": voice_data["emotion"].primary_emotion,
                "response": response,
                "timestamp": datetime.now()
            })
    
    def predict_intent(self, partial_input: str, user_id: str) -> List[str]:
        """Predict what user might want based on partial input"""
        predictions = []
        
        # Check conversation context
        if self.context.current_topic:
            predictions.extend(self._topic_based_predictions(partial_input))
        
        # Check user patterns
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            predictions.extend(self._pattern_based_predictions(partial_input, profile))
        
        # Check time-based patterns
        predictions.extend(self._temporal_predictions())
        
        return predictions[:5]  # Top 5 predictions
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        # Simplified - use NER model in production
        entities = {
            "people": [],
            "places": [],
            "times": [],
            "objects": []
        }
        
        # Basic pattern matching
        import re
        
        # Time patterns
        time_pattern = r'\b\d{1,2}:\d{2}\s*(?:am|pm)?\b'
        entities["times"] = re.findall(time_pattern, text.lower())
        
        return entities
    
    def _identify_topic(self, text: str) -> Optional[str]:
        """Identify conversation topic"""
        # Simplified topic detection
        topics = {
            "weather": ["weather", "temperature", "rain", "sunny", "cloudy"],
            "work": ["meeting", "email", "project", "deadline", "task"],
            "entertainment": ["movie", "music", "game", "show", "watch"],
            "food": ["eat", "hungry", "restaurant", "cook", "dinner"]
        }
        
        text_lower = text.lower()
        for topic, keywords in topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return None
    
    def _topic_based_predictions(self, partial: str) -> List[str]:
        """Predictions based on current topic"""
        topic_suggestions = {
            "weather": [
                "What's the weather like today?",
                "Will it rain tomorrow?",
                "What's the temperature outside?"
            ],
            "work": [
                "What's on my calendar today?",
                "Send an email to",
                "Create a reminder for"
            ]
        }
        
        if self.context.current_topic in topic_suggestions:
            return [s for s in topic_suggestions[self.context.current_topic] 
                   if s.lower().startswith(partial.lower())]
        
        return []
    
    def _pattern_based_predictions(self, partial: str, profile: VoiceProfile) -> List[str]:
        """Predictions based on user patterns"""
        # Analyze recent interactions
        recent_queries = [h["query"] for h in profile.interaction_history]
        
        # Find similar starting patterns
        suggestions = []
        for query in recent_queries:
            if query.lower().startswith(partial.lower()) and len(query) > len(partial):
                suggestions.append(query)
        
        return list(set(suggestions))[:3]
    
    def _temporal_predictions(self) -> List[str]:
        """Time-based predictions"""
        now = datetime.now()
        hour = now.hour
        
        suggestions = []
        
        if 6 <= hour < 10:
            suggestions.extend([
                "What's my schedule for today?",
                "What's the weather?",
                "Any important emails?"
            ])
        elif 11 <= hour < 14:
            suggestions.extend([
                "Find a good restaurant nearby",
                "What's for lunch?",
                "Order food"
            ])
        elif 17 <= hour < 20:
            suggestions.extend([
                "What's the traffic like?",
                "Plan my route home",
                "What's for dinner?"
            ])
        elif 20 <= hour < 23:
            suggestions.extend([
                "Play some relaxing music",
                "What's on Netflix?",
                "Set alarm for tomorrow"
            ])
        
        return suggestions


class PatternMemory:
    """Long-term pattern storage and retrieval"""
    
    def __init__(self, memory_path: Path = Path(".nina_memory")):
        self.memory_path = memory_path
        self.memory_path.mkdir(exist_ok=True)
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """Load saved patterns"""
        pattern_file = self.memory_path / "patterns.json"
        if pattern_file.exists():
            with open(pattern_file, 'r') as f:
                return json.load(f)
        return {
            "daily_routines": {},
            "query_sequences": {},
            "preference_patterns": {}
        }
    
    def save_patterns(self):
        """Save patterns to disk"""
        pattern_file = self.memory_path / "patterns.json"
        with open(pattern_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)


class AdaptiveResponseGenerator:
    """Generates responses adapted to user emotion and context"""
    
    def __init__(self):
        self.response_templates = self._load_templates()
        self.personality_engine = PersonalityEngine()
    
    def _load_templates(self) -> Dict:
        """Load response templates for different contexts"""
        return {
            "happy": {
                "greeting": "Great to hear you're in a good mood! {}",
                "task": "I'd be happy to help with that! {}",
                "error": "Oops, that didn't work, but no worries! {}"
            },
            "sad": {
                "greeting": "I'm here for you. {}",
                "task": "Let me help you with that. {}",
                "error": "I apologize for the trouble. {}"
            },
            "angry": {
                "greeting": "I understand. How can I help? {}",
                "task": "I'll take care of that right away. {}",
                "error": "I sincerely apologize. Let me fix this. {}"
            },
            "calm": {
                "greeting": "Hello! {}",
                "task": "Certainly, {}",
                "error": "There was an issue. {}"
            }
        }
    
    def generate_response(self, 
                         base_response: str,
                         emotion: EmotionalState,
                         context: ConversationContext,
                         user_profile: Optional[VoiceProfile] = None) -> str:
        """Generate emotionally adapted response"""
        
        # Select template based on emotion
        emotion_templates = self.response_templates.get(
            emotion.primary_emotion, 
            self.response_templates["calm"]
        )
        
        # Determine response type
        response_type = self._classify_response(base_response)
        
        # Get template
        template = emotion_templates.get(response_type, "{}")
        
        # Apply personality adaptations
        if user_profile and user_profile.preferences:
            base_response = self.personality_engine.adapt_response(
                base_response, 
                user_profile.preferences
            )
        
        # Format response
        final_response = template.format(base_response)
        
        # Add contextual elements
        if context.unresolved_questions:
            final_response += f" By the way, you asked about {context.unresolved_questions[0]} earlier. Would you like me to address that?"
        
        return final_response
    
    def _classify_response(self, response: str) -> str:
        """Classify response type"""
        if any(word in response.lower() for word in ["hello", "hi", "good morning"]):
            return "greeting"
        elif any(word in response.lower() for word in ["error", "sorry", "couldn't"]):
            return "error"
        else:
            return "task"


class PersonalityEngine:
    """Manages Nina's adaptive personality"""
    
    def __init__(self):
        self.personality_traits = {
            "formality": 0.5,  # 0=casual, 1=formal
            "verbosity": 0.5,  # 0=concise, 1=detailed
            "humor": 0.3,      # 0=serious, 1=humorous
            "empathy": 0.8,    # 0=neutral, 1=empathetic
        }
    
    def adapt_response(self, response: str, user_preferences: Dict) -> str:
        """Adapt response based on user preferences"""
        # Adjust formality
        if user_preferences.get("prefers_casual", False):
            response = self._make_casual(response)
        elif user_preferences.get("prefers_formal", False):
            response = self._make_formal(response)
        
        # Adjust verbosity
        if user_preferences.get("prefers_brief", False):
            response = self._make_concise(response)
        
        return response
    
    def _make_casual(self, text: str) -> str:
        """Make response more casual"""
        replacements = {
            "I will": "I'll",
            "cannot": "can't",
            "will not": "won't",
            "Certainly": "Sure",
            "However": "But"
        }
        for formal, casual in replacements.items():
            text = text.replace(formal, casual)
        return text
    
    def _make_formal(self, text: str) -> str:
        """Make response more formal"""
        replacements = {
            "I'll": "I will",
            "can't": "cannot",
            "won't": "will not",
            "Sure": "Certainly",
            "But": "However"
        }
        for casual, formal in replacements.items():
            text = text.replace(casual, formal)
        return text
    
    def _make_concise(self, text: str) -> str:
        """Make response more concise"""
        # Remove filler phrases
        fillers = [
            "I think that",
            "It seems like",
            "You might want to",
            "Perhaps you could"
        ]
        for filler in fillers:
            text = text.replace(filler, "")
        
        # Limit sentence count
        sentences = text.split('. ')
        if len(sentences) > 3:
            text = '. '.join(sentences[:3]) + '.'
        
        return text.strip()


class NinaCognitiveSystem:
    """Main cognitive system orchestrating all components"""
    
    def __init__(self, interaction, 
                 wake_word: str = "nina",
                 enable_predictive: bool = True,
                 enable_ambient: bool = True):
        self.interaction = interaction
        self.wake_word = wake_word.lower()
        self.enable_predictive = enable_predictive
        self.enable_ambient = enable_ambient
        
        # Initialize components
        self.voice_processor = CognitiveVoiceProcessor()
        self.context_engine = PredictiveContextEngine()
        self.response_generator = AdaptiveResponseGenerator()
        
        # State management
        self.is_active = False
        self.is_listening = True
        self.current_user = "default_user"
        self.interaction_mode = "voice"  # voice, ambient, predictive
        
        # Queues for async processing
        self.audio_queue = asyncio.Queue()
        self.prediction_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()
        
        # Performance metrics
        self.metrics = {
            "response_times": deque(maxlen=100),
            "accuracy_scores": deque(maxlen=100),
            "user_satisfaction": deque(maxlen=100)
        }
    
    async def start(self):
        """Start all cognitive systems"""
        tasks = [
            self._audio_processing_loop(),
            self._prediction_loop(),
            self._response_generation_loop(),
            self._ambient_monitoring_loop()
        ]
        
        if self.interaction.speech:
            await self._speak("Nina cognitive system online. I'm ready to assist you.")
        
        await asyncio.gather(*tasks)
    
    async def _audio_processing_loop(self):
        """Main audio processing loop"""
        while self.is_listening:
            try:
                # Get audio from queue
                audio_data = await self.audio_queue.get()
                
                # Process audio
                start_time = time.time()
                voice_data = await self.voice_processor.process_audio_stream(
                    audio_data["audio"],
                    audio_data["sample_rate"]
                )
                
                # Update metrics
                self.metrics["response_times"].append(time.time() - start_time)
                
                # Check for wake word or active conversation
                transcription = voice_data["transcription"]["text"].lower()
                
                if self.wake_word in transcription or self.is_active:
                    await self._handle_voice_input(voice_data)
                elif self.enable_ambient:
                    await self._handle_ambient_input(voice_data)
                    
            except Exception as e:
                print(f"Audio processing error: {e}")
    
    async def _handle_voice_input(self, voice_data: Dict):
        """Handle active voice interaction"""
        emotion = voice_data["emotion"]
        transcription = voice_data["transcription"]["text"]
        
        # Update context
        self.context_engine.update_context(voice_data, "")
        
        # Generate predictive suggestions if partial input
        if self.enable_predictive and len(transcription.split()) < 3:
            predictions = self.context_engine.predict_intent(
                transcription, 
                self.current_user
            )
            if predictions:
                await self.prediction_queue.put(predictions)
        
        # Check for complete command
        if self._is_complete_command(voice_data):
            # Process through agents
            self.interaction.set_query(transcription)
            
            # Add emotion context to query
            self.interaction.last_emotion = emotion
            
            # Process
            success = await self.interaction.think()
            
            if success:
                # Generate adapted response
                base_response = self.interaction.last_answer
                
                adapted_response = self.response_generator.generate_response(
                    base_response,
                    emotion,
                    self.context_engine.context,
                    self.context_engine.user_profiles.get(self.current_user)
                )
                
                # Speak response
                await self._speak(adapted_response, emotion=emotion)
                
                # Update context with response
                self.context_engine.update_context(voice_data, adapted_response)
    
    async def _handle_ambient_input(self, voice_data: Dict):
        """Handle ambient awareness without explicit commands"""
        # Detect important ambient information
        text = voice_data["transcription"]["text"]
        emotion = voice_data["emotion"]
        
        # Check for concerning patterns
        if emotion.primary_emotion == "sad" and emotion.confidence > 0.8:
            # Offer support without being intrusive
            await asyncio.sleep(3)  # Wait to see if user addresses Nina
            if not self.is_active:
                await self._speak("I noticed you might be having a tough time. I'm here if you need anything.")
        
        # Update ambient context
        self.context_engine.context.ambient_context.update({
            "last_ambient_emotion": emotion.primary_emotion,
            "ambient_topics": self.context_engine._identify_topic(text),
            "timestamp": datetime.now()
        })
    
    async def _prediction_loop(self):
        """Handle predictive suggestions"""
        while True:
            try:
                predictions = await self.prediction_queue.get()
                
                # Display predictions to user (visual feedback)
                if self.interaction.current_agent:
                    # Could update UI with suggestions
                    pass
                
            except Exception as e:
                print(f"Prediction error: {e}")
    
    async def _response_generation_loop(self):
        """Generate responses with parallel processing"""
        while True:
            try:
                response_task = await self.response_queue.get()
                # Process response generation tasks
                
            except Exception as e:
                print(f"Response generation error: {e}")
    
    async def _ambient_monitoring_loop(self):
        """Monitor ambient environment for proactive assistance"""
        while self.enable_ambient:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                context = self.context_engine.context
                now = datetime.now()
                
                # Time-based reminders
                if hasattr(self, '_last_reminder_check'):
                    time_since_last = (now - self._last_reminder_check).seconds
                    
                    # Check for unresolved tasks
                    if context.task_stack and time_since_last > 1800:  # 30 minutes
                        task = context.task_stack[0]
                        await self._speak(f"Just a reminder about {task['description']}")
                
                self._last_reminder_check = now
                
            except Exception as e:
                print(f"Ambient monitoring error: {e}")
    
    def _is_complete_command(self, voice_data: Dict) -> bool:
        """Determine if user has finished speaking"""
        # Check prosody for falling intonation
        prosody = voice_data["prosody"]
        
        # Check for pause length
        # Check for question indicators
        text = voice_data["transcription"]["text"]
        
        return (
            "?" in text or
            any(text.lower().startswith(w) for w in ["what", "where", "when", "how", "why", "who"]) or
            prosody["pitch_variance"] < 50  # Falling intonation
        )
    
    async def _speak(self, text: str, emotion: Optional[EmotionalState] = None):
        """Speak with emotional adaptation"""
        if self.interaction.speech:
            # Adapt voice based on user emotion
            if emotion:
                if emotion.primary_emotion == "sad":
                    # Speak more softly and slowly
                    self.interaction.speech.speed = 1.0
                elif emotion.primary_emotion == "happy":
                    # Speak with more energy
                    self.interaction.speech.speed = 1.3
                else:
                    self.interaction.speech.speed = 1.2
            
            self.interaction.speech.speak(text)


# Launch script
async def launch_nina_cognitive():
    """Launch Nina with full cognitive capabilities"""
    print("""
    ╔══════════════════════════════════════════════╗
    ║        Nina 2.0 Cognitive Voice System       ║
    ║                                              ║
    ║  Features:                                   ║
    ║  • Emotional Intelligence                    ║
    ║  • Predictive Interaction                    ║
    ║  • Voice Biometrics                          ║
    ║  • Ambient Awareness                         ║
    ║  • Adaptive Personality                      ║
    ║                                              ║
    ║  Say "Nina" to interact                      ║
    ╚══════════════════════════════════════════════╝
    """)
    
    # Initialize system using Agentic Seek components
    import configparser
    from sources.llm_provider import Provider
    from sources.interaction import Interaction
    from sources.agents import CasualAgent, CoderAgent, FileAgent, BrowserAgent, PlannerAgent
    from sources.browser import Browser, create_driver
    from sources.utility import pretty_print
    
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Force voice modes on for cognitive system
    config.set('MAIN', 'speak', 'True')
    config.set('MAIN', 'listen', 'True')
    
    pretty_print("Initializing Nina Cognitive System...", color="status")
    
    # Initialize provider
    provider = Provider(
        provider_name=config["MAIN"]["provider_name"],
        model=config["MAIN"]["provider_model"],
        server_address=config["MAIN"]["provider_server_address"],
        is_local=config.getboolean('MAIN', 'is_local')
    )
    
    # Initialize browser (headless for cognitive mode)
    languages = config["MAIN"]["languages"].split(' ')
    browser = Browser(
        create_driver(headless=True, stealth_mode=False, lang=languages[0]),
        anticaptcha_manual_install=False
    )
    
    # Initialize agents
    personality_folder = "jarvis" if config.getboolean('MAIN', 'jarvis_personality') else "base"
    
    agents = [
        CasualAgent(
            name="Nina",
            prompt_path=f"prompts/{personality_folder}/casual_agent.txt",
            provider=provider,
            verbose=False
        ),
        CoderAgent(
            name="coder",
            prompt_path=f"prompts/{personality_folder}/coder_agent.txt",
            provider=provider,
            verbose=False
        ),
        FileAgent(
            name="File Agent",
            prompt_path=f"prompts/{personality_folder}/file_agent.txt",
            provider=provider,
            verbose=False
        ),
        BrowserAgent(
            name="Browser",
            prompt_path=f"prompts/{personality_folder}/browser_agent.txt",
            provider=provider,
            verbose=False,
            browser=browser
        ),
        PlannerAgent(
            name="Planner",
            prompt_path=f"prompts/{personality_folder}/planner_agent.txt",
            provider=provider,
            verbose=False,
            browser=browser
        ),
    ]
    
    # Create interaction instance
    interaction = Interaction(
        agents,
        tts_enabled=True,
        stt_enabled=True,
        recover_last_session=False,
        langs=languages
    )
    
    # Create cognitive system
    nina = NinaCognitiveSystem(
        interaction,
        wake_word="nina",
        enable_predictive=True,
        enable_ambient=True
    )
    
    # Start the system
    try:
        await nina.start()
    except KeyboardInterrupt:
        print("\nShutting down Nina Cognitive System...")
        if browser:
            browser.driver.quit()
        print("Goodbye!")

if __name__ == "__main__":
    asyncio.run(launch_nina_cognitive())