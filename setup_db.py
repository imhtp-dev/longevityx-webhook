from datetime import datetime, timedelta, timezone
import sqlite3

DB_FILE = "tokens.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Token table (solo 1 riga)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            expires_in INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # User Profile (dati statici)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            email TEXT,
            first_name TEXT,
            last_name TEXT
        )
    """)

    # Cycles
    c.execute("""
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            start TEXT,
            end TEXT,
            timezone_offset TEXT,
            strain REAL,
            kilojoule REAL,
            avg_heart_rate INTEGER,
            max_heart_rate INTEGER
        )
    """)

    # Recoveries
    c.execute("""
        CREATE TABLE IF NOT EXISTS recoveries (
            cycle_id INTEGER PRIMARY KEY,
            sleep_id INTEGER,
            user_id INTEGER,
            recovery_score INTEGER,
            resting_heart_rate INTEGER,
            hrv_rmssd_milli REAL,
            spo2_percentage REAL,
            skin_temp_celsius REAL
        )
    """)

    # Sleep
    c.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            start TEXT,
            end TEXT,
            timezone_offset TEXT,
            nap INTEGER,
            total_in_bed_time_milli INTEGER,
            total_awake_time_milli INTEGER,
            total_light_sleep_time_milli INTEGER,
            total_slow_wave_sleep_time_milli INTEGER,
            total_rem_sleep_time_milli INTEGER,
            sleep_cycle_count INTEGER,
            disturbance_count INTEGER,
            respiratory_rate REAL,
            sleep_performance_percentage INTEGER,
            sleep_consistency_percentage INTEGER,
            sleep_efficiency_percentage REAL
        )
    """)

    # workouts
    c.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            created_at TEXT,
            updated_at TEXT,
            start TEXT,
            end TEXT,
            timezone_offset TEXT,
            sport_id INTEGER,
            score_state TEXT,
            strain REAL,
            average_heart_rate INTEGER,
            max_heart_rate INTEGER,
            kilojoule REAL,
            percent_recorded INTEGER,
            distance_meter REAL,
            altitude_gain_meter REAL,
            altitude_change_meter REAL,
            zone_zero_milli INTEGER,
            zone_one_milli INTEGER,
            zone_two_milli INTEGER,
            zone_three_milli INTEGER,
            zone_four_milli INTEGER,
            zone_five_milli INTEGER
        )
    """)


    print("[DB] Database ready.")
    conn.commit()
    conn.close()

####TOKENS


def save_tokens(access_token, refresh_token, expires_in):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO tokens (id, access_token, refresh_token, expires_in)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            access_token=excluded.access_token,
            refresh_token=excluded.refresh_token,
            expires_in=excluded.expires_in,
            timestamp=CURRENT_TIMESTAMP
    """, (access_token, refresh_token, expires_in))
    print("[DB] Tokens saved/updated.")
    conn.commit()
    conn.close()

def get_latest_tokens():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT id, access_token, refresh_token, expires_in, timestamp FROM tokens
        WHERE id = 1
    """)
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "access_token": row[1],
            "refresh_token": row[2],
            "expires_in": row[3],
            "timestamp": row[4],
        }
    print("[DB] No tokens found.")
    return None


#### INSERT



def insert_sleep(data):
    score = data.get("score", {})
    stage = score.get("stage_summary", {})

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO sleep (
            id, user_id, start, end, timezone_offset, nap,
            total_in_bed_time_milli, total_awake_time_milli, total_light_sleep_time_milli,
            total_slow_wave_sleep_time_milli, total_rem_sleep_time_milli, sleep_cycle_count,
            disturbance_count, respiratory_rate, sleep_performance_percentage,
            sleep_consistency_percentage, sleep_efficiency_percentage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["id"],
        data["user_id"],
        data.get("start"),
        data.get("end"),
        data.get("timezone_offset"),
        int(data.get("nap", False)),
        stage.get("total_in_bed_time_milli"),
        stage.get("total_awake_time_milli"),
        stage.get("total_light_sleep_time_milli"),
        stage.get("total_slow_wave_sleep_time_milli"),
        stage.get("total_rem_sleep_time_milli"),
        stage.get("sleep_cycle_count"),
        stage.get("disturbance_count"),
        score.get("respiratory_rate"),
        score.get("sleep_performance_percentage"),
        score.get("sleep_consistency_percentage"),
        score.get("sleep_efficiency_percentage")
    ))
    conn.commit()
    conn.close()



def insert_workout(workout):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        INSERT OR REPLACE INTO workouts (
            id, user_id, created_at, updated_at, start, end, timezone_offset,
            sport_id, score_state, strain, average_heart_rate, max_heart_rate,
            kilojoule, percent_recorded, distance_meter, altitude_gain_meter,
            altitude_change_meter, zone_zero_milli, zone_one_milli,
            zone_two_milli, zone_three_milli, zone_four_milli, zone_five_milli
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        workout['id'],
        workout['user_id'],
        workout['created_at'],
        workout['updated_at'],
        workout['start'],
        workout['end'],
        workout['timezone_offset'],
        workout['sport_id'],
        workout['score_state'],
        workout['score']['strain'],
        workout['score']['average_heart_rate'],
        workout['score']['max_heart_rate'],
        workout['score']['kilojoule'],
        workout['score']['percent_recorded'],
        workout['score']['distance_meter'],
        workout['score']['altitude_gain_meter'],
        workout['score']['altitude_change_meter'],
        workout['score']['zone_duration']['zone_zero_milli'],
        workout['score']['zone_duration']['zone_one_milli'],
        workout['score']['zone_duration']['zone_two_milli'],
        workout['score']['zone_duration']['zone_three_milli'],
        workout['score']['zone_duration']['zone_four_milli'],
        workout['score']['zone_duration']['zone_five_milli'],
    ))

    conn.commit()
    conn.close()

###retrieve

def get_sleep_data(last_days=30):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    since = (datetime.now(timezone.utc) - timedelta(days=last_days)).isoformat()

    cursor.execute('''
        SELECT * FROM sleep
        WHERE start >= ?
        ORDER BY start DESC
    ''', (since,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]



def get_workout_data(last_days=30):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    since = (datetime.now(timezone.utc) - timedelta(days=last_days)).isoformat()

    cursor.execute('''
        SELECT * FROM workouts
        WHERE start >= ?
        ORDER BY start DESC
    ''', (since,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
