import django
from django.conf import settings
from django.db import models, connections
from datetime import datetime
import json
from .game_types import Tournament
from sys import stderr
import os


# Database class for handling database operations via Django database connection
class Database:
    def __init__(self, engine='django.db.backends.postgresql_psycopg2'):
        self.Model = None

        databases = {
            'default': {
                'ENGINE': engine,
                'NAME': os.getenv('POSTGRES_DB'),
                'USER': os.getenv('POSTGRES_USER'),
                'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
                'HOST': os.getenv('POSTGRES_HOST'),
                'PORT': '5432',
                'APP_LABEL': 'frontapp',
            }
        }

        settings.configure(DATABASES=databases)
        django.setup()

        class CustomBaseModel(models.Model):
            class Meta:
                app_label = 'frontapp'
                abstract = True

        self.Model = CustomBaseModel

    def game_result_to_user_stats(self, player_id, is_winner, p2_wins, score):
        try:
            print(f"game_result_to_user_stats: Player ID: {player_id}, is_winner: {is_winner}, p2_wins: {p2_wins}, score: {score}", file=stderr)
            sql_query = "SELECT stats FROM auth_user WHERE id = %s;"
            with connections['default'].cursor() as cursor:
                cursor.execute(sql_query, [player_id])
                print(f"Player ID: {player_id}")
                stats = cursor.fetchone()[0]

            stats = json.loads(stats)
            stats['games_played'] = stats.get('games_played', 0) + 1
            if is_winner == 1:
                stats['games_won'] = stats.get('games_won', 0) + 1
            else:
                stats['games_lost'] = stats.get('games_lost', 0) + 1
            if score:
                stats['score'] = stats.get('score', 0) + score
            stats = json.dumps(stats)

            sql_query = "UPDATE auth_user SET stats = %s WHERE id = %s;"
            with connections['default'].cursor() as cursor:
                cursor.execute(sql_query, [stats, player_id])
        except Exception as e:
            print(f'game_result_to_user_stats: {e}', file=stderr)

    def add_game(self, player1, player2, winner, p1_wins, p2_wins):
        sql_query = """
        INSERT INTO frontapp_game (player1_id, player2_id, winner_id, p1_wins, p2_wins, date)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        current_time = datetime.now()
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, (player1, player2, winner, p1_wins, p2_wins, current_time))

    def add_tournament(self, tournament: Tournament):
        try:
            sql_query = """
            INSERT INTO frontapp_tournament (creator_id, name, number_of_players, start_time, status, winner_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            with connections['default'].cursor() as cursor:
                cursor.execute(sql_query, (tournament.creator, tournament.name, tournament.number_of_players, tournament.start_time, tournament.status, tournament.winner))
                cursor.execute("SELECT LASTVAL();")
                inserted_row_id = cursor.fetchone()[0]
            print(f'XXXXXXXXXXXXX: inserted_row_id = {inserted_row_id}')
            return inserted_row_id
        except Exception as e:
            print(f'add_tournament: {e}', file=stderr)
    
    def delete_tournament(self, tournament_id):
        print(f"Deleting tournament {tournament_id}")
        # First, delete any dependent Tournament-customuser relationships for this tournament
        delete_relationships_sql = "DELETE FROM frontapp_tournament_players WHERE tournament_id = %s;"
        # Then, delete the tournament
        delete_tournament_sql = "DELETE FROM frontapp_tournament WHERE id = %s;"
        
        with connections['default'].cursor() as cursor:
            cursor.execute(delete_relationships_sql, [tournament_id])
            cursor.execute(delete_tournament_sql, [tournament_id])
    
    # On game_service start, all open tournaments in the db are deleted, because they can not be handled anymore and are invalid
    def delete_all_tournaments(self):
        # First, delete any dependent Tournament-customuser relationships
        delete_relationships_sql = "DELETE FROM frontapp_tournament_players WHERE tournament_id IN (SELECT id FROM frontapp_tournament);"
        # Then, delete the tournaments
        delete_tournaments_sql = "DELETE FROM frontapp_tournament;"
        
        with connections['default'].cursor() as cursor:
            cursor.execute(delete_relationships_sql)
            cursor.execute(delete_tournaments_sql)

    def change_tournament_status(self, tournament_id, status):
        sql_query = "UPDATE frontapp_tournament SET status = %s WHERE id = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [status, tournament_id])

    def get_display_names(self, player_ids):
        # Generate placeholders for each item in player_ids
        placeholders = ','.join(['%s'] * len(player_ids))
        sql_query = f"SELECT id, display_name FROM auth_user WHERE id IN ({placeholders});"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, player_ids)
            result = {row[0]: row[1] for row in cursor.fetchall()}
        return result
    
    def get_display_name(self, player_id):
        sql_query = "SELECT display_name FROM auth_user WHERE id = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [player_id])
            result = cursor.fetchone()
        return result[0] if result else None

    def add_player_to_tournament(self, tournament_id, player_id):
        print(f"Adding players to tournament {tournament_id}: {player_id}")
        join_table = 'tournament_players'
        tournament_col = 'tournament_id'
        player_col = 'customuser_id'
        sql_query = f"INSERT INTO frontapp_{join_table} ({tournament_col}, {player_col}) VALUES (%s, %s);"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [tournament_id, player_id])

    def delete_player_from_tournament(self, tournament_id, player_id):
        print(f"Deleting player {player_id} from tournament {tournament_id}")
        join_table = 'tournament_players'
        tournament_col = 'tournament_id'
        player_col = 'customuser_id'
        sql_query = f"DELETE FROM frontapp_{join_table} WHERE {tournament_col} = %s AND {player_col} = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [tournament_id, player_id])
        
