#!/usr/bin/env python3
"""
Pokemon TCG Tracker - Analytics Service
Advanced analytics and statistics calculations for match and deck performance.
"""

from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for calculating advanced analytics and statistics."""
    
    def __init__(self):
        """Initialize the analytics service."""
        logger.info("📊 Analytics service initialized")
    
    # ==================================================================================
    # BASIC STATISTICS
    # ==================================================================================
    
    def calculate_win_rate(self, matches: List[Dict[str, Any]]) -> float:
        """Calculate overall win rate percentage."""
        if not matches:
            return 0.0
        
        wins = sum(1 for match in matches if match.get('result') == 'Win')
        win_rate = round((wins / len(matches)) * 100, 1)
        
        logger.info(f"📊 Calculated win rate: {win_rate}% ({wins}/{len(matches)})")
        return win_rate
    
    def calculate_deck_performance(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance statistics for all decks."""
        deck_stats = defaultdict(lambda: {
            'games': 0, 
            'wins': 0, 
            'total_turns': 0, 
            'games_with_turns': 0,
            'first_player_games': 0,
            'first_player_wins': 0,
            'win_conditions': defaultdict(int),
            'opponents_faced': defaultdict(int),
            'recent_form': []  # Last 10 games
        })
        
        for match in matches:
            deck_name = match.get('myDeck', '')
            if not deck_name:
                continue
            
            stats = deck_stats[deck_name]
            stats['games'] += 1
            
            # Win tracking
            if match.get('result') == 'Win':
                stats['wins'] += 1
            
            # Turn tracking
            if match.get('turns') and str(match['turns']).isdigit():
                stats['total_turns'] += int(match['turns'])
                stats['games_with_turns'] += 1
            
            # First player tracking
            if match.get('wentFirst') == 'You':
                stats['first_player_games'] += 1
                if match.get('result') == 'Win':
                    stats['first_player_wins'] += 1
            
            # Win condition tracking
            win_condition = match.get('winCondition', '')
            if win_condition and match.get('result') == 'Win':
                stats['win_conditions'][win_condition] += 1
            
            # Opponent tracking
            opponent = match.get('opponentDeck', '')
            if opponent:
                stats['opponents_faced'][opponent] += 1
            
            # Recent form (last 10 games)
            stats['recent_form'].append(match.get('result', 'Loss'))
            if len(stats['recent_form']) > 10:
                stats['recent_form'].pop(0)
        
        # Calculate final statistics
        performance = {}
        for deck_name, stats in deck_stats.items():
            win_rate = round((stats['wins'] / stats['games']) * 100, 1) if stats['games'] > 0 else 0
            avg_turns = round(stats['total_turns'] / stats['games_with_turns'], 1) if stats['games_with_turns'] > 0 else 0
            first_player_rate = round((stats['first_player_wins'] / stats['first_player_games']) * 100, 1) if stats['first_player_games'] > 0 else 0
            
            # Recent form calculation (last 10 games)
            recent_wins = sum(1 for result in stats['recent_form'] if result == 'Win')
            recent_form_rate = round((recent_wins / len(stats['recent_form'])) * 100, 1) if stats['recent_form'] else 0
            
            performance[deck_name] = {
                'games': stats['games'],
                'wins': stats['wins'],
                'losses': stats['games'] - stats['wins'],
                'win_rate': win_rate,
                'avg_turns': avg_turns,
                'first_player_games': stats['first_player_games'],
                'first_player_win_rate': first_player_rate,
                'most_common_win_condition': max(stats['win_conditions'].items(), key=lambda x: x[1])[0] if stats['win_conditions'] else None,
                'most_faced_opponent': max(stats['opponents_faced'].items(), key=lambda x: x[1])[0] if stats['opponents_faced'] else None,
                'recent_form': stats['recent_form'],
                'recent_form_rate': recent_form_rate
            }
        
        logger.info(f"📊 Calculated performance for {len(performance)} decks")
        return dict(performance)
    
    # ==================================================================================
    # MATCHUP ANALYSIS
    # ==================================================================================
    
    def calculate_matchup_analysis(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detailed matchup analysis."""
        # Deck vs Deck analysis
        deck_matchups = defaultdict(lambda: defaultdict(lambda: {'games': 0, 'wins': 0}))
        
        # Card analysis
        card_performance = defaultdict(lambda: {'faced': 0, 'wins': 0, 'losses': 0})
        
        # Combination analysis (deck + card)
        combo_analysis = defaultdict(lambda: {'faced': 0, 'wins': 0, 'losses': 0})
        
        for match in matches:
            my_deck = match.get('myDeck', '')
            opponent_deck = match.get('opponentDeck', '')
            result = match.get('result', 'Loss')
            notable_cards = match.get('notableCards', '')
            
            # Deck vs Deck matchups
            if my_deck and opponent_deck:
                matchup = deck_matchups[my_deck][opponent_deck]
                matchup['games'] += 1
                if result == 'Win':
                    matchup['wins'] += 1
            
            # Card analysis
            if notable_cards:
                cards = [card.strip() for card in notable_cards.split(',') if card.strip()]
                for card in cards:
                    card_stats = card_performance[card]
                    card_stats['faced'] += 1
                    if result == 'Win':
                        card_stats['wins'] += 1
                    else:
                        card_stats['losses'] += 1
            
            # Combination analysis
            if opponent_deck and notable_cards:
                cards = [card.strip() for card in notable_cards.split(',') if card.strip()]
                for card in cards:
                    combo_key = f"{opponent_deck} + {card}"
                    combo_stats = combo_analysis[combo_key]
                    combo_stats['faced'] += 1
                    if result == 'Win':
                        combo_stats['wins'] += 1
                    else:
                        combo_stats['losses'] += 1
        
        # Process deck matchups
        processed_matchups = {}
        for my_deck, opponents in deck_matchups.items():
            processed_matchups[my_deck] = {}
            for opponent_deck, stats in opponents.items():
                win_rate = round((stats['wins'] / stats['games']) * 100, 1) if stats['games'] > 0 else 0
                processed_matchups[my_deck][opponent_deck] = {
                    'games': stats['games'],
                    'wins': stats['wins'],
                    'losses': stats['games'] - stats['wins'],
                    'win_rate': win_rate
                }
        
        # Process card performance (sort by loss rate for problem cards)
        problem_cards = []
        for card, stats in card_performance.items():
            if stats['faced'] >= 2:  # Only cards faced multiple times
                loss_rate = round((stats['losses'] / stats['faced']) * 100, 1)
                problem_cards.append({
                    'card': card,
                    'faced': stats['faced'],
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'loss_rate': loss_rate
                })
        
        problem_cards.sort(key=lambda x: x['loss_rate'], reverse=True)
        
        # Process combination analysis
        deadly_combos = []
        for combo, stats in combo_analysis.items():
            if stats['faced'] >= 2:  # Only combos faced multiple times
                loss_rate = round((stats['losses'] / stats['faced']) * 100, 1)
                deadly_combos.append({
                    'combo': combo,
                    'faced': stats['faced'],
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'loss_rate': loss_rate
                })
        
        deadly_combos.sort(key=lambda x: x['loss_rate'], reverse=True)
        
        analysis = {
            'deck_matchups': processed_matchups,
            'problem_cards': problem_cards[:10],  # Top 10 problem cards
            'deadly_combos': deadly_combos[:10],  # Top 10 deadly combos
            'total_unique_opponents': len(set(match.get('opponentDeck', '') for match in matches if match.get('opponentDeck'))),
            'total_unique_cards_faced': len(card_performance)
        }
        
        logger.info(f"📊 Calculated matchup analysis: {analysis['total_unique_opponents']} opponents, {analysis['total_unique_cards_faced']} unique cards")
        return analysis
    
    # ==================================================================================
    # TURN ORDER ANALYSIS
    # ==================================================================================
    
    def calculate_first_player_advantage(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate first player advantage statistics."""
        first_player_stats = {'games': 0, 'wins': 0}
        second_player_stats = {'games': 0, 'wins': 0}
        
        # Per-deck first player analysis
        deck_first_player = defaultdict(lambda: {
            'first_games': 0, 'first_wins': 0,
            'second_games': 0, 'second_wins': 0
        })
        
        for match in matches:
            went_first = match.get('wentFirst', '')
            result = match.get('result', 'Loss')
            deck = match.get('myDeck', '')
            
            if went_first == 'You':
                first_player_stats['games'] += 1
                if result == 'Win':
                    first_player_stats['wins'] += 1
                
                if deck:
                    deck_stats = deck_first_player[deck]
                    deck_stats['first_games'] += 1
                    if result == 'Win':
                        deck_stats['first_wins'] += 1
                        
            elif went_first in ['Opp', 'Opponent']:
                second_player_stats['games'] += 1
                if result == 'Win':
                    second_player_stats['wins'] += 1
                
                if deck:
                    deck_stats = deck_first_player[deck]
                    deck_stats['second_games'] += 1
                    if result == 'Win':
                        deck_stats['second_wins'] += 1
        
        # Calculate overall rates
        first_player_rate = round((first_player_stats['wins'] / first_player_stats['games']) * 100, 1) if first_player_stats['games'] > 0 else 0
        second_player_rate = round((second_player_stats['wins'] / second_player_stats['games']) * 100, 1) if second_player_stats['games'] > 0 else 0
        advantage = first_player_rate - second_player_rate
        
        # Calculate per-deck rates
        deck_analysis = {}
        for deck, stats in deck_first_player.items():
            first_rate = round((stats['first_wins'] / stats['first_games']) * 100, 1) if stats['first_games'] > 0 else 0
            second_rate = round((stats['second_wins'] / stats['second_games']) * 100, 1) if stats['second_games'] > 0 else 0
            deck_advantage = first_rate - second_rate
            
            deck_analysis[deck] = {
                'first_player_games': stats['first_games'],
                'first_player_wins': stats['first_wins'],
                'first_player_rate': first_rate,
                'second_player_games': stats['second_games'],
                'second_player_wins': stats['second_wins'],
                'second_player_rate': second_rate,
                'advantage': deck_advantage
            }
        
        analysis = {
            'overall': {
                'first_player_games': first_player_stats['games'],
                'first_player_wins': first_player_stats['wins'],
                'first_player_rate': first_player_rate,
                'second_player_games': second_player_stats['games'],
                'second_player_wins': second_player_stats['wins'],
                'second_player_rate': second_player_rate,
                'advantage': advantage
            },
            'by_deck': deck_analysis,
            'total_games_with_turn_data': first_player_stats['games'] + second_player_stats['games']
        }
        
        logger.info(f"📊 Calculated first player advantage: {advantage:+.1f}% overall")
        return analysis
    
    # ==================================================================================
    # WIN CONDITION ANALYSIS
    # ==================================================================================
    
    def calculate_win_condition_breakdown(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate win condition breakdown statistics."""
        win_conditions = [
            'Prize Cards Taken',
            'No Benched Pokemon', 
            'Deck Milled',
            'Conceded',
            'Conceded first turn'
        ]
        
        overall_stats = {}
        deck_stats = defaultdict(lambda: defaultdict(lambda: {'your_wins': 0, 'opponent_wins': 0}))
        
        # Initialize stats
        for condition in win_conditions:
            overall_stats[condition] = {'your_wins': 0, 'opponent_wins': 0}
        
        # Process matches
        for match in matches:
            win_condition = match.get('winCondition', '')
            result = match.get('result', 'Loss')
            deck = match.get('myDeck', '')
            
            if win_condition in win_conditions:
                # Overall stats
                if result == 'Win':
                    overall_stats[win_condition]['your_wins'] += 1
                else:
                    overall_stats[win_condition]['opponent_wins'] += 1
                
                # Per-deck stats
                if deck:
                    if result == 'Win':
                        deck_stats[deck][win_condition]['your_wins'] += 1
                    else:
                        deck_stats[deck][win_condition]['opponent_wins'] += 1
        
        # Calculate percentages for overall stats
        processed_overall = {}
        for condition, stats in overall_stats.items():
            total = stats['your_wins'] + stats['opponent_wins']
            if total > 0:
                your_percentage = round((stats['your_wins'] / total) * 100, 1)
                processed_overall[condition] = {
                    'your_wins': stats['your_wins'],
                    'opponent_wins': stats['opponent_wins'],
                    'total': total,
                    'your_percentage': your_percentage
                }
        
        # Calculate percentages for deck stats
        processed_deck_stats = {}
        for deck, conditions in deck_stats.items():
            processed_deck_stats[deck] = {}
            for condition, stats in conditions.items():
                total = stats['your_wins'] + stats['opponent_wins']
                if total > 0:
                    your_percentage = round((stats['your_wins'] / total) * 100, 1)
                    processed_deck_stats[deck][condition] = {
                        'your_wins': stats['your_wins'],
                        'opponent_wins': stats['opponent_wins'],
                        'total': total,
                        'your_percentage': your_percentage
                    }
        
        # Find most/least effective win conditions
        effectiveness_ranking = []
        for condition, stats in processed_overall.items():
            effectiveness_ranking.append({
                'condition': condition,
                'percentage': stats['your_percentage'],
                'total_games': stats['total']
            })
        
        effectiveness_ranking.sort(key=lambda x: x['percentage'], reverse=True)
        
        analysis = {
            'overall': processed_overall,
            'by_deck': dict(processed_deck_stats),
            'effectiveness_ranking': effectiveness_ranking,
            'most_effective': effectiveness_ranking[0]['condition'] if effectiveness_ranking else None,
            'least_effective': effectiveness_ranking[-1]['condition'] if effectiveness_ranking else None
        }
        
        logger.info(f"📊 Calculated win condition breakdown for {len(processed_overall)} conditions")
        return analysis
    
    # ==================================================================================
    # GAME PACING ANALYSIS
    # ==================================================================================
    
    def calculate_game_pacing_analysis(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate game pacing and turn statistics."""
        games_with_turns = [
            match for match in matches 
            if match.get('turns') and str(match['turns']).isdigit()
        ]
        
        if not games_with_turns:
            return {
                'total_games_with_turn_data': 0,
                'overall': {},
                'by_result': {},
                'by_deck': {},
                'turn_distribution': {}
            }
        
        # Overall statistics
        all_turns = [int(match['turns']) for match in games_with_turns]
        win_turns = [int(match['turns']) for match in games_with_turns if match.get('result') == 'Win']
        loss_turns = [int(match['turns']) for match in games_with_turns if match.get('result') == 'Loss']
        
        overall_stats = {
            'avg_turns': round(sum(all_turns) / len(all_turns), 1),
            'min_turns': min(all_turns),
            'max_turns': max(all_turns),
            'median_turns': sorted(all_turns)[len(all_turns) // 2]
        }
        
        # By result statistics
        by_result = {
            'wins': {
                'count': len(win_turns),
                'avg_turns': round(sum(win_turns) / len(win_turns), 1) if win_turns else 0,
                'min_turns': min(win_turns) if win_turns else 0,
                'max_turns': max(win_turns) if win_turns else 0
            },
            'losses': {
                'count': len(loss_turns),
                'avg_turns': round(sum(loss_turns) / len(loss_turns), 1) if loss_turns else 0,
                'min_turns': min(loss_turns) if loss_turns else 0,
                'max_turns': max(loss_turns) if loss_turns else 0
            }
        }
        
        # Fast win analysis (games won in 7 turns or less)
        fast_wins = [match for match in games_with_turns if match.get('result') == 'Win' and int(match['turns']) <= 7]
        fast_win_rate = round((len(fast_wins) / len(win_turns)) * 100, 1) if win_turns else 0
        
        # By deck statistics
        deck_pacing = defaultdict(list)
        for match in games_with_turns:
            deck = match.get('myDeck', '')
            if deck:
                deck_pacing[deck].append(int(match['turns']))
        
        by_deck = {}
        for deck, turns_list in deck_pacing.items():
            by_deck[deck] = {
                'games': len(turns_list),
                'avg_turns': round(sum(turns_list) / len(turns_list), 1),
                'min_turns': min(turns_list),
                'max_turns': max(turns_list)
            }
        
        # Turn distribution
        turn_distribution = Counter(all_turns)
        distribution_percentages = {}
        total_games = len(all_turns)
        for turns, count in turn_distribution.items():
            distribution_percentages[turns] = {
                'count': count,
                'percentage': round((count / total_games) * 100, 1)
            }
        
        analysis = {
            'total_games_with_turn_data': len(games_with_turns),
            'overall': overall_stats,
            'by_result': by_result,
            'by_deck': dict(by_deck),
            'turn_distribution': dict(distribution_percentages),
            'fast_wins': {
                'count': len(fast_wins),
                'rate': fast_win_rate,
                'definition': 'Games won in 7 turns or less'
            }
        }
        
        logger.info(f"📊 Calculated game pacing for {len(games_with_turns)} games with turn data")
        return analysis
    
    # ==================================================================================
    # TREND ANALYSIS
    # ==================================================================================
    
    def calculate_trend_analysis(self, matches: List[Dict[str, Any]], days: int = 30) -> Dict[str, Any]:
        """Calculate performance trends over time."""
        if not matches:
            return {'period_days': days, 'trends': {}}
        
        # Sort matches by date
        dated_matches = []
        for match in matches:
            try:
                if match.get('timestamp'):
                    match_date = datetime.fromisoformat(match['timestamp'].replace('Z', '+00:00'))
                elif match.get('date'):
                    match_date = datetime.strptime(match['date'], '%Y-%m-%d')
                else:
                    continue
                dated_matches.append((match_date, match))
            except (ValueError, TypeError):
                continue
        
        dated_matches.sort(key=lambda x: x[0])
        
        # Define periods
        now = datetime.now()
        recent_cutoff = now - timedelta(days=days)
        
        recent_matches = [match for date, match in dated_matches if date >= recent_cutoff]
        older_matches = [match for date, match in dated_matches if date < recent_cutoff]
        
        def calculate_period_stats(period_matches):
            if not period_matches:
                return {'games': 0, 'wins': 0, 'win_rate': 0}
            
            wins = sum(1 for match in period_matches if match.get('result') == 'Win')
            return {
                'games': len(period_matches),
                'wins': wins,
                'losses': len(period_matches) - wins,
                'win_rate': round((wins / len(period_matches)) * 100, 1)
            }
        
        recent_stats = calculate_period_stats(recent_matches)
        older_stats = calculate_period_stats(older_matches)
        
        # Calculate trend
        if older_stats['games'] > 0:
            trend = recent_stats['win_rate'] - older_stats['win_rate']
            trend_direction = 'improving' if trend > 5 else 'declining' if trend < -5 else 'stable'
        else:
            trend = 0
            trend_direction = 'new'
        
        # Weekly breakdown for recent period
        weekly_stats = defaultdict(lambda: {'games': 0, 'wins': 0})
        for date, match in dated_matches:
            if date >= recent_cutoff:
                week_start = date - timedelta(days=date.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                
                weekly_stats[week_key]['games'] += 1
                if match.get('result') == 'Win':
                    weekly_stats[week_key]['wins'] += 1
        
        # Process weekly stats
        weekly_breakdown = {}
        for week, stats in weekly_stats.items():
            win_rate = round((stats['wins'] / stats['games']) * 100, 1) if stats['games'] > 0 else 0
            weekly_breakdown[week] = {
                'games': stats['games'],
                'wins': stats['wins'],
                'losses': stats['games'] - stats['wins'],
                'win_rate': win_rate
            }
        
        analysis = {
            'period_days': days,
            'recent_period': recent_stats,
            'previous_period': older_stats,
            'trend': {
                'change': round(trend, 1),
                'direction': trend_direction
            },
            'weekly_breakdown': weekly_breakdown,
            'total_tracked_matches': len(dated_matches)
        }
        
        logger.info(f"📊 Calculated trend analysis: {trend_direction} trend ({trend:+.1f}%)")
        return analysis
    
    # ==================================================================================
    # COMPREHENSIVE REPORT
    # ==================================================================================
    
    def generate_comprehensive_report(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive analytics report."""
        logger.info("📊 Generating comprehensive analytics report...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_matches': len(matches),
            'basic_stats': {
                'overall_win_rate': self.calculate_win_rate(matches),
                'total_wins': sum(1 for m in matches if m.get('result') == 'Win'),
                'total_losses': sum(1 for m in matches if m.get('result') == 'Loss')
            },
            'deck_performance': self.calculate_deck_performance(matches),
            'matchup_analysis': self.calculate_matchup_analysis(matches),
            'first_player_advantage': self.calculate_first_player_advantage(matches),
            'win_condition_breakdown': self.calculate_win_condition_breakdown(matches),
            'game_pacing': self.calculate_game_pacing_analysis(matches),
            'trend_analysis': self.calculate_trend_analysis(matches, days=30)
        }
        
        # Add summary insights
        insights = []
        
        # Win rate insight
        win_rate = report['basic_stats']['overall_win_rate']
        if win_rate >= 60:
            insights.append(f"🎉 Excellent overall performance with {win_rate}% win rate!")
        elif win_rate >= 50:
            insights.append(f"✅ Solid performance with {win_rate}% win rate")
        else:
            insights.append(f"📈 Room for improvement - current win rate is {win_rate}%")
        
        # First player advantage insight
        fp_advantage = report['first_player_advantage']['overall']['advantage']
        if abs(fp_advantage) > 10:
            direction = "going first" if fp_advantage > 0 else "going second"
            insights.append(f"🎯 Strong preference for {direction} ({fp_advantage:+.1f}% advantage)")
        
        # Trend insight
        trend = report['trend_analysis']['trend']
        if trend['direction'] == 'improving':
            insights.append(f"📈 Recent performance is improving (+{trend['change']:.1f}%)")
        elif trend['direction'] == 'declining':
            insights.append(f"📉 Recent performance needs attention ({trend['change']:.1f}%)")
        
        report['insights'] = insights
        
        logger.info(f"✅ Generated comprehensive report with {len(insights)} insights")
        return report