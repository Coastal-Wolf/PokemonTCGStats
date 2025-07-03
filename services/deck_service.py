#!/usr/bin/env python3
"""
Pokemon TCG Tracker - Deck Service
Handles all deck-related data operations and deck building logic.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DeckService:
    """Service for managing deck data and deck building operations."""
    
    def __init__(self, autosave_service):
        """Initialize the deck service with autosave capability."""
        self.autosave_service = autosave_service
        
        logger.info("🃏 Deck service initialized")
    
    def _get_data(self) -> Dict[str, Any]:
        """Get all data from storage."""
        try:
            return self.autosave_service.load_data()
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            return self.autosave_service.get_default_data()
    
    def _save_data(self, data: Dict[str, Any]) -> bool:
        """Save all data to storage."""
        try:
            return self.autosave_service.save_data(
                data['matches'],
                data['decks'],
                data['deck_history'],
                data['current_deck']
            )
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")
            return False
    
    # ==================================================================================
    # DECK MANAGEMENT
    # ==================================================================================
    
    def get_all_decks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all decks."""
        data = self._get_data()
        decks = data.get('decks', {})
        logger.info(f"🃏 Retrieved {len(decks)} decks")
        return decks
    
    def get_deck(self, deck_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get a specific deck by name."""
        decks = self.get_all_decks()
        
        if deck_name in decks:
            deck = decks[deck_name]
            logger.info(f"🎯 Retrieved deck '{deck_name}' with {len(deck)} cards")
            return deck
        else:
            logger.warning(f"⚠️ Deck '{deck_name}' not found")
            return None
    
    def create_deck(self, deck_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deck."""
        try:
            deck_name = deck_data.get('name', '').strip()
            if not deck_name:
                raise ValueError("Deck name is required")
            
            cards = deck_data.get('cards', [])
            
            # Validate and clean card data
            clean_cards = []
            for card in cards:
                clean_card = self._validate_and_clean_card_data(card)
                clean_cards.append(clean_card)
            
            data = self._get_data()
            
            # Check if deck already exists
            if deck_name in data['decks']:
                raise ValueError(f"Deck '{deck_name}' already exists")
            
            # Add the new deck
            data['decks'][deck_name] = clean_cards
            
            # Add history entry
            self._add_history_entry_internal(data, {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'change': 'Created',
                'cards': f'New deck with {len(clean_cards)} cards',
                'reason': f'Created deck: {deck_name}'
            })
            
            # Save to storage
            if self._save_data(data):
                logger.info(f"✅ Created deck '{deck_name}' with {len(clean_cards)} cards")
                return {
                    'name': deck_name,
                    'cards': clean_cards,
                    'total_cards': sum(card['count'] for card in clean_cards)
                }
            else:
                raise Exception("Failed to save deck")
                
        except Exception as e:
            logger.error(f"❌ Failed to create deck: {e}")
            raise
    
    def update_deck(self, deck_name: str, deck_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing deck."""
        try:
            data = self._get_data()
            
            if deck_name not in data['decks']:
                logger.warning(f"⚠️ Deck '{deck_name}' not found for update")
                return None
            
            cards = deck_data.get('cards', [])
            
            # Validate and clean card data
            clean_cards = []
            for card in cards:
                clean_card = self._validate_and_clean_card_data(card)
                clean_cards.append(clean_card)
            
            # Update the deck
            old_count = len(data['decks'][deck_name])
            data['decks'][deck_name] = clean_cards
            
            # Add history entry
            self._add_history_entry_internal(data, {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'change': 'Modified',
                'cards': f'{old_count}→{len(clean_cards)} cards',
                'reason': f'Updated deck: {deck_name}'
            })
            
            # Save to storage
            if self._save_data(data):
                logger.info(f"📝 Updated deck '{deck_name}' with {len(clean_cards)} cards")
                return {
                    'name': deck_name,
                    'cards': clean_cards,
                    'total_cards': sum(card['count'] for card in clean_cards)
                }
            else:
                raise Exception("Failed to save updated deck")
                
        except Exception as e:
            logger.error(f"❌ Failed to update deck '{deck_name}': {e}")
            raise
    
    def delete_deck(self, deck_name: str) -> bool:
        """Delete a deck."""
        try:
            data = self._get_data()
            
            if deck_name not in data['decks']:
                logger.warning(f"⚠️ Deck '{deck_name}' not found for deletion")
                return False
            
            # Remove the deck
            deleted_deck = data['decks'].pop(deck_name)
            
            # If this was the current deck, set a new one
            if data['current_deck'] == deck_name:
                remaining_decks = list(data['decks'].keys())
                data['current_deck'] = remaining_decks[0] if remaining_decks else ''
            
            # Add history entry
            self._add_history_entry_internal(data, {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'change': 'Deleted',
                'cards': f'Removed deck with {len(deleted_deck)} cards',
                'reason': f'Deleted deck: {deck_name}'
            })
            
            # Save to storage
            if self._save_data(data):
                logger.info(f"🗑️ Deleted deck '{deck_name}'")
                return True
            else:
                # Restore the deck if save failed
                data['decks'][deck_name] = deleted_deck
                raise Exception("Failed to save after deletion")
                
        except Exception as e:
            logger.error(f"❌ Failed to delete deck '{deck_name}': {e}")
            return False
    
    def bulk_update_decks(self, decks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Update all decks in bulk (used for auto-save)."""
        try:
            # Validate and clean all deck data
            clean_decks = {}
            for deck_name, cards in decks.items():
                if not isinstance(deck_name, str) or not deck_name.strip():
                    logger.warning(f"⚠️ Skipping invalid deck name: {deck_name}")
                    continue
                
                clean_cards = []
                for card in cards:
                    try:
                        clean_card = self._validate_and_clean_card_data(card)
                        clean_cards.append(clean_card)
                    except Exception as e:
                        logger.warning(f"⚠️ Skipping invalid card in deck '{deck_name}': {e}")
                        continue
                
                clean_decks[deck_name.strip()] = clean_cards
            
            # Update data
            data = self._get_data()
            data['decks'] = clean_decks
            
            # Save to storage
            if self._save_data(data):
                logger.info(f"💾 Bulk updated {len(clean_decks)} decks")
                return True
            else:
                raise Exception("Failed to save bulk deck update")
                
        except Exception as e:
            logger.error(f"❌ Failed to bulk update decks: {e}")
            return False
    
    # ==================================================================================
    # CARD MANAGEMENT
    # ==================================================================================
    
    def add_card_to_deck(self, deck_name: str, card_data: Dict[str, Any]) -> bool:
        """Add a card to a deck."""
        try:
            data = self._get_data()
            
            if deck_name not in data['decks']:
                raise ValueError(f"Deck '{deck_name}' not found")
            
            clean_card = self._validate_and_clean_card_data(card_data)
            
            # Check if card already exists in deck
            existing_card_index = None
            for i, card in enumerate(data['decks'][deck_name]):
                if card['name'].lower() == clean_card['name'].lower():
                    existing_card_index = i
                    break
            
            if existing_card_index is not None:
                # Update existing card count
                old_count = data['decks'][deck_name][existing_card_index]['count']
                data['decks'][deck_name][existing_card_index]['count'] = clean_card['count']
                
                change_desc = f"{clean_card['name']} ({old_count}→{clean_card['count']})"
                change_type = 'Modified'
            else:
                # Add new card
                data['decks'][deck_name].append(clean_card)
                change_desc = f"{clean_card['name']} ({clean_card['count']})"
                change_type = 'Added'
            
            # Add history entry
            self._add_history_entry_internal(data, {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'change': change_type,
                'cards': change_desc,
                'reason': f'Card modification in {deck_name}'
            })
            
            # Save to storage
            if self._save_data(data):
                logger.info(f"✅ {change_type} card in deck '{deck_name}': {change_desc}")
                return True
            else:
                raise Exception("Failed to save card addition")
                
        except Exception as e:
            logger.error(f"❌ Failed to add card to deck '{deck_name}': {e}")
            return False
    
    def remove_card_from_deck(self, deck_name: str, card_name: str) -> bool:
        """Remove a card from a deck."""
        try:
            data = self._get_data()
            
            if deck_name not in data['decks']:
                raise ValueError(f"Deck '{deck_name}' not found")
            
            # Find and remove the card
            card_removed = False
            for i, card in enumerate(data['decks'][deck_name]):
                if card['name'].lower() == card_name.lower():
                    removed_card = data['decks'][deck_name].pop(i)
                    card_removed = True
                    break
            
            if not card_removed:
                logger.warning(f"⚠️ Card '{card_name}' not found in deck '{deck_name}'")
                return False
            
            # Add history entry
            self._add_history_entry_internal(data, {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'change': 'Removed',
                'cards': f"{removed_card['name']} ({removed_card['count']})",
                'reason': f'Removed card from {deck_name}'
            })
            
            # Save to storage
            if self._save_data(data):
                logger.info(f"🗑️ Removed card from deck '{deck_name}': {removed_card['name']}")
                return True
            else:
                # Restore the card if save failed
                data['decks'][deck_name].insert(i, removed_card)
                raise Exception("Failed to save card removal")
                
        except Exception as e:
            logger.error(f"❌ Failed to remove card from deck '{deck_name}': {e}")
            return False
    
    def _validate_and_clean_card_data(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean card data."""
        if not isinstance(card_data, dict):
            raise ValueError("Card data must be a dictionary")
        
        # Required fields
        name = card_data.get('name', '').strip()
        if not name:
            raise ValueError("Card name is required")
        
        # Validate count
        try:
            count = int(card_data.get('count', 1))
            if count < 1:
                count = 1
        except (ValueError, TypeError):
            count = 1
        
        # Validate type
        card_type = card_data.get('type', 'Pokemon').strip()
        valid_types = ['Pokemon', 'Trainer', 'Energy']
        if card_type not in valid_types:
            card_type = 'Pokemon'
        
        # Set maximum count based on type
        max_count = 30 if card_type == 'Energy' else 4
        if count > max_count:
            count = max_count
        
        return {
            'name': name,
            'count': count,
            'type': card_type
        }
    
    # ==================================================================================
    # DECK HISTORY
    # ==================================================================================
    
    def get_deck_history(self) -> List[Dict[str, Any]]:
        """Get deck modification history."""
        data = self._get_data()
        history = data.get('deck_history', [])
        logger.info(f"📚 Retrieved {len(history)} history entries")
        return history
    
    def add_history_entry(self, history_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a deck history entry."""
        try:
            data = self._get_data()
            entry = self._add_history_entry_internal(data, history_data)
            
            if self._save_data(data):
                logger.info(f"📝 Added history entry: {entry['change']}")
                return entry
            else:
                raise Exception("Failed to save history entry")
                
        except Exception as e:
            logger.error(f"❌ Failed to add history entry: {e}")
            raise
    
    def _add_history_entry_internal(self, data: Dict[str, Any], history_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to add history entry to data."""
        entry = {
            'date': history_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'change': history_data.get('change', 'Modified'),
            'cards': history_data.get('cards', ''),
            'reason': history_data.get('reason', 'Manual modification')
        }
        
        if 'deck_history' not in data:
            data['deck_history'] = []
        
        data['deck_history'].append(entry)
        return entry
    
    def bulk_update_history(self, history: List[Dict[str, Any]]) -> bool:
        """Update deck history in bulk (used for auto-save)."""
        try:
            # Validate history entries
            clean_history = []
            for entry in history:
                if isinstance(entry, dict):
                    clean_entry = {
                        'date': entry.get('date', datetime.now().strftime('%Y-%m-%d')),
                        'change': entry.get('change', 'Modified'),
                        'cards': entry.get('cards', ''),
                        'reason': entry.get('reason', 'Manual modification')
                    }
                    clean_history.append(clean_entry)
            
            # Update data
            data = self._get_data()
            data['deck_history'] = clean_history
            
            # Save to storage
            if self._save_data(data):
                logger.info(f"💾 Bulk updated {len(clean_history)} history entries")
                return True
            else:
                raise Exception("Failed to save bulk history update")
                
        except Exception as e:
            logger.error(f"❌ Failed to bulk update history: {e}")
            return False
    
    # ==================================================================================
    # CURRENT DECK
    # ==================================================================================
    
    def get_current_deck(self) -> str:
        """Get the currently selected deck."""
        data = self._get_data()
        current_deck = data.get('current_deck', '')
        
        # Ensure the current deck still exists
        if current_deck and current_deck not in data.get('decks', {}):
            # Set to first available deck
            available_decks = list(data.get('decks', {}).keys())
            current_deck = available_decks[0] if available_decks else ''
            
            # Update and save
            data['current_deck'] = current_deck
            self._save_data(data)
        
        logger.info(f"🎯 Current deck: {current_deck or 'None'}")
        return current_deck
    
    def set_current_deck(self, deck_name: str) -> bool:
        """Set the currently selected deck."""
        try:
            data = self._get_data()
            
            if deck_name and deck_name not in data.get('decks', {}):
                raise ValueError(f"Deck '{deck_name}' not found")
            
            data['current_deck'] = deck_name
            
            if self._save_data(data):
                logger.info(f"🎯 Set current deck to: {deck_name}")
                return True
            else:
                raise Exception("Failed to save current deck")
                
        except Exception as e:
            logger.error(f"❌ Failed to set current deck: {e}")
            return False
    
    # ==================================================================================
    # DECK ANALYSIS
    # ==================================================================================
    
    def get_deck_statistics(self, deck_name: str) -> Dict[str, Any]:
        """Get statistics for a specific deck."""
        deck = self.get_deck(deck_name)
        if not deck:
            return {}
        
        total_cards = sum(card['count'] for card in deck)
        
        # Count by type
        type_counts = {}
        for card in deck:
            card_type = card['type']
            if card_type not in type_counts:
                type_counts[card_type] = {'cards': 0, 'count': 0}
            type_counts[card_type]['cards'] += 1
            type_counts[card_type]['count'] += card['count']
        
        return {
            'name': deck_name,
            'unique_cards': len(deck),
            'total_cards': total_cards,
            'type_breakdown': type_counts,
            'is_tournament_legal': self._is_tournament_legal(deck),
            'completion_percentage': self._calculate_completion_percentage(deck)
        }
    
    def _is_tournament_legal(self, deck: List[Dict[str, Any]]) -> bool:
        """Check if a deck is tournament legal."""
        total_cards = sum(card['count'] for card in deck)
        
        # Basic checks (these can be adjusted based on actual tournament rules)
        if total_cards < 60:  # Minimum deck size
            return False
        
        # Check individual card limits
        for card in deck:
            if card['type'] != 'Energy' and card['count'] > 4:
                return False
        
        return True
    
    def _calculate_completion_percentage(self, deck: List[Dict[str, Any]]) -> float:
        """Calculate deck completion percentage."""
        total_cards = sum(card['count'] for card in deck)
        target_size = 60  # Standard deck size
        
        return min(100.0, (total_cards / target_size) * 100)
    
    def suggest_deck_improvements(self, deck_name: str) -> List[str]:
        """Suggest improvements for a deck."""
        deck = self.get_deck(deck_name)
        if not deck:
            return []
        
        suggestions = []
        stats = self.get_deck_statistics(deck_name)
        
        # Size suggestions
        if stats['total_cards'] < 60:
            suggestions.append(f"Add {60 - stats['total_cards']} more cards to reach minimum deck size")
        
        # Type balance suggestions
        type_counts = stats['type_breakdown']
        if 'Pokemon' in type_counts and type_counts['Pokemon']['count'] < 10:
            suggestions.append("Consider adding more Pokemon for better consistency")
        
        if 'Energy' in type_counts and type_counts['Energy']['count'] < 12:
            suggestions.append("Consider adding more Energy cards for better resource management")
        
        if 'Trainer' in type_counts and type_counts['Trainer']['count'] < 20:
            suggestions.append("Consider adding more Trainer cards for deck utility")
        
        return suggestions