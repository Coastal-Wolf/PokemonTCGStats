#!/usr/bin/env python3
"""
Pokemon TCG Tracker - Match Service
Handles all match-related data operations and business logic.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MatchService:
    """Service for managing match data operations."""
    
    def __init__(self, autosave_service):
        """Initialize the match service with autosave capability."""
        self.autosave_service = autosave_service
        self._matches_cache = None
        self._cache_timestamp = None
        
        logger.info("⚔️ Match service initialized")
    
    def _get_matches(self) -> List[Dict[str, Any]]:
        """Get matches from cache or load from storage."""
        try:
            data = self.autosave_service.load_data()
            return data.get('matches', [])
        except Exception as e:
            logger.error(f"❌ Failed to load matches: {e}")
            return []
    
    def _save_matches(self, matches: List[Dict[str, Any]]) -> bool:
        """Save matches to storage."""
        try:
            data = self.autosave_service.load_data()
            data['matches'] = matches
            
            return self.autosave_service.save_data(
                matches,
                data['decks'],
                data['deck_history'],
                data['current_deck']
            )
        except Exception as e:
            logger.error(f"❌ Failed to save matches: {e}")
            return False
    
    def get_all_matches(self) -> List[Dict[str, Any]]:
        """Get all matches."""
        matches = self._get_matches()
        logger.info(f"📊 Retrieved {len(matches)} matches")
        return matches
    
    def get_match_by_id(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific match by ID (index)."""
        matches = self._get_matches()
        
        if 0 <= match_id < len(matches):
            return matches[match_id]
        else:
            logger.warning(f"⚠️ Match ID {match_id} not found")
            return None
    
    def create_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new match."""
        try:
            # Validate and clean match data
            clean_match = self._validate_and_clean_match_data(match_data)
            
            # Add timestamp if not present
            if 'timestamp' not in clean_match:
                clean_match['timestamp'] = datetime.now().isoformat()
            
            # Load current matches and add new one
            matches = self._get_matches()
            matches.append(clean_match)
            
            # Save to storage
            if self._save_matches(matches):
                logger.info(f"✅ Created match: {clean_match.get('myDeck', 'Unknown')} vs {clean_match.get('opponentDeck', 'Unknown')} - {clean_match.get('result', 'Unknown')}")
                return clean_match
            else:
                raise Exception("Failed to save match")
                
        except Exception as e:
            logger.error(f"❌ Failed to create match: {e}")
            raise
    
    def update_match(self, match_id: int, match_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing match."""
        try:
            matches = self._get_matches()
            
            if 0 <= match_id < len(matches):
                # Validate and clean the updated data
                clean_match = self._validate_and_clean_match_data(match_data)
                
                # Preserve original timestamp if not provided
                if 'timestamp' not in clean_match and 'timestamp' in matches[match_id]:
                    clean_match['timestamp'] = matches[match_id]['timestamp']
                elif 'timestamp' not in clean_match:
                    clean_match['timestamp'] = datetime.now().isoformat()
                
                # Update the match
                matches[match_id] = clean_match
                
                # Save to storage
                if self._save_matches(matches):
                    logger.info(f"📝 Updated match {match_id}: {clean_match.get('myDeck', 'Unknown')} vs {clean_match.get('opponentDeck', 'Unknown')}")
                    return clean_match
                else:
                    raise Exception("Failed to save updated match")
            else:
                logger.warning(f"⚠️ Match ID {match_id} not found for update")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to update match {match_id}: {e}")
            raise
    
    def delete_match(self, match_id: int) -> bool:
        """Delete a match."""
        try:
            matches = self._get_matches()
            
            if 0 <= match_id < len(matches):
                deleted_match = matches.pop(match_id)
                
                # Save to storage
                if self._save_matches(matches):
                    logger.info(f"🗑️ Deleted match {match_id}: {deleted_match.get('myDeck', 'Unknown')} vs {deleted_match.get('opponentDeck', 'Unknown')}")
                    return True
                else:
                    # Restore the match if save failed
                    matches.insert(match_id, deleted_match)
                    raise Exception("Failed to save after deletion")
            else:
                logger.warning(f"⚠️ Match ID {match_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete match {match_id}: {e}")
            return False
    
    def bulk_update_matches(self, matches: List[Dict[str, Any]]) -> bool:
        """Update all matches in bulk (used for auto-save)."""
        try:
            # Validate and clean all matches
            clean_matches = []
            for i, match in enumerate(matches):
                try:
                    clean_match = self._validate_and_clean_match_data(match)
                    clean_matches.append(clean_match)
                except Exception as e:
                    logger.warning(f"⚠️ Skipping invalid match {i}: {e}")
                    continue
            
            # Save to storage
            if self._save_matches(clean_matches):
                logger.info(f"💾 Bulk updated {len(clean_matches)} matches")
                return True
            else:
                raise Exception("Failed to save bulk update")
                
        except Exception as e:
            logger.error(f"❌ Failed to bulk update matches: {e}")
            return False
    
    def _validate_and_clean_match_data(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean match data."""
        # Required fields with defaults
        required_fields = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'myDeck': '',
            'opponentDeck': '',
            'result': 'Loss',
            'turns': '',
            'wentFirst': 'You',
            'winCondition': 'Prize Cards Taken',
            'notableCards': '',
            'notes': ''
        }
        
        # Start with defaults
        clean_match = required_fields.copy()
        
        # Update with provided data
        for key, value in match_data.items():
            if key in required_fields or key == 'timestamp':
                clean_match[key] = value
        
        # Validate specific fields
        if clean_match['result'] not in ['Win', 'Loss']:
            clean_match['result'] = 'Loss'
        
        if clean_match['wentFirst'] not in ['You', 'Opp', 'Opponent']:
            clean_match['wentFirst'] = 'You'
        
        # Handle "Opponent" legacy value
        if clean_match['wentFirst'] == 'Opponent':
            clean_match['wentFirst'] = 'Opp'
        
        valid_win_conditions = [
            'Prize Cards Taken',
            'No Benched Pokemon', 
            'Deck Milled',
            'Conceded',
            'Conceded first turn'
        ]
        if clean_match['winCondition'] not in valid_win_conditions:
            clean_match['winCondition'] = 'Prize Cards Taken'
        
        # Validate turns field
        if clean_match['turns'] is not None and clean_match['turns'] != '':
            try:
                turns_value = int(clean_match['turns'])
                if turns_value < 1 or turns_value > 50:
                    clean_match['turns'] = ''
                else:
                    clean_match['turns'] = turns_value
            except (ValueError, TypeError):
                clean_match['turns'] = ''
        
        # Ensure timestamp exists
        if 'timestamp' not in clean_match:
            if clean_match['date']:
                clean_match['timestamp'] = f"{clean_match['date']}T12:00:00"
            else:
                clean_match['timestamp'] = datetime.now().isoformat()
        
        # Clean string fields
        string_fields = ['myDeck', 'opponentDeck', 'notableCards', 'notes']
        for field in string_fields:
            if isinstance(clean_match[field], str):
                clean_match[field] = clean_match[field].strip()
        
        return clean_match
    
    def get_matches_by_deck(self, deck_name: str) -> List[Dict[str, Any]]:
        """Get all matches for a specific deck."""
        matches = self._get_matches()
        deck_matches = [match for match in matches if match.get('myDeck') == deck_name]
        logger.info(f"🃏 Found {len(deck_matches)} matches for deck '{deck_name}'")
        return deck_matches
    
    def get_matches_vs_opponent(self, opponent_deck: str) -> List[Dict[str, Any]]:
        """Get all matches against a specific opponent deck."""
        matches = self._get_matches()
        opponent_matches = [match for match in matches if match.get('opponentDeck') == opponent_deck]
        logger.info(f"🎯 Found {len(opponent_matches)} matches vs '{opponent_deck}'")
        return opponent_matches
    
    def get_recent_matches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent matches."""
        matches = self._get_matches()
        
        # Sort by timestamp (newest first)
        sorted_matches = sorted(
            matches,
            key=lambda m: m.get('timestamp', ''),
            reverse=True
        )
        
        recent = sorted_matches[:limit]
        logger.info(f"⏰ Retrieved {len(recent)} recent matches")
        return recent
    
    def search_matches(self, query: str) -> List[Dict[str, Any]]:
        """Search matches by deck names, cards, or notes."""
        matches = self._get_matches()
        query_lower = query.lower()
        
        matching_matches = []
        for match in matches:
            # Search in relevant fields
            search_fields = [
                match.get('myDeck', ''),
                match.get('opponentDeck', ''),
                match.get('notableCards', ''),
                match.get('notes', ''),
                match.get('winCondition', '')
            ]
            
            if any(query_lower in str(field).lower() for field in search_fields):
                matching_matches.append(match)
        
        logger.info(f"🔍 Found {len(matching_matches)} matches for query '{query}'")
        return matching_matches
    
    def get_win_loss_record(self) -> Dict[str, int]:
        """Get overall win/loss record."""
        matches = self._get_matches()
        
        wins = len([m for m in matches if m.get('result') == 'Win'])
        losses = len([m for m in matches if m.get('result') == 'Loss'])
        
        return {
            'wins': wins,
            'losses': losses,
            'total': wins + losses,
            'win_rate': round((wins / (wins + losses)) * 100, 1) if (wins + losses) > 0 else 0
        }
    
    def get_match_statistics(self) -> Dict[str, Any]:
        """Get comprehensive match statistics."""
        matches = self._get_matches()
        
        if not matches:
            return {
                'total_matches': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'average_turns': 0,
                'fastest_win': None,
                'longest_game': None
            }
        
        wins = len([m for m in matches if m.get('result') == 'Win'])
        losses = len([m for m in matches if m.get('result') == 'Loss'])
        
        # Calculate turn statistics
        matches_with_turns = [m for m in matches if m.get('turns') and str(m['turns']).isdigit()]
        if matches_with_turns:
            turns_list = [int(m['turns']) for m in matches_with_turns]
            avg_turns = sum(turns_list) / len(turns_list)
            fastest_win = min([int(m['turns']) for m in matches_with_turns if m.get('result') == 'Win'], default=None)
            longest_game = max(turns_list)
        else:
            avg_turns = 0
            fastest_win = None
            longest_game = None
        
        return {
            'total_matches': len(matches),
            'wins': wins,
            'losses': losses,
            'win_rate': round((wins / len(matches)) * 100, 1),
            'average_turns': round(avg_turns, 1),
            'fastest_win': fastest_win,
            'longest_game': longest_game,
            'unique_decks_played': len(set(m.get('myDeck', '') for m in matches if m.get('myDeck'))),
            'unique_opponents_faced': len(set(m.get('opponentDeck', '') for m in matches if m.get('opponentDeck')))
        }
    
    def export_matches_csv(self) -> str:
        """Export matches to CSV format."""
        matches = self._get_matches()
        
        # CSV header
        csv_lines = ['Date,Timestamp,My Deck,Opponent Deck,Result,Turns,Went First,Win Condition,Notable Cards,Notes']
        
        # Add each match
        for match in matches:
            line = ','.join([
                f'"{match.get("date", "")}"',
                f'"{match.get("timestamp", "")}"',
                f'"{match.get("myDeck", "")}"',
                f'"{match.get("opponentDeck", "")}"',
                f'"{match.get("result", "")}"',
                f'"{match.get("turns", "")}"',
                f'"{match.get("wentFirst", "")}"',
                f'"{match.get("winCondition", "")}"',
                f'"{match.get("notableCards", "")}"',
                f'"{match.get("notes", "")}"'
            ])
            csv_lines.append(line)
        
        csv_content = '\n'.join(csv_lines)
        logger.info(f"📁 Exported {len(matches)} matches to CSV")
        return csv_content