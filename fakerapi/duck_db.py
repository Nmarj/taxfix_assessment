import duckdb
import pandas as pd
from typing import Optional, Dict, List, Tuple, Any

class DuckDBManager:
    """Manager for DuckDB operations."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
    
    def __enter__(self):
        self.conn = duckdb.connect(self.db_path)
        self._create_table()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
    
    def _create_table(self):
        """Create the persons table with appropriate schema."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS persons (
            id VARCHAR PRIMARY KEY,
            domain VARCHAR,
            age_group VARCHAR,
            city VARCHAR,
            country VARCHAR,
            country_code VARCHAR,
            street VARCHAR,
            street_name VARCHAR,
            building_number VARCHAR,
            zipcode VARCHAR,
            latitude VARCHAR,
            longitude VARCHAR,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
        self.conn.execute(create_table_sql)
    
    def insert_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Insert a batch of records into DuckDB.
        
        Args:
            records: List of validated person records
            
        Returns:
            Number of records inserted
        """
        if not records:
            return 0
        
        df = pd.DataFrame(records)
        
        # Insert into DuckDB
        self.conn.register('persons_virtual_table', df)
        self.conn.execute("""
            INSERT INTO persons (id, domain, age_group, city, country, 
                                country_code, street, street_name, building_number, zipcode, latitude, longitude)
            SELECT id, domain, age_group, city, country,country_code, street, street_name, building_number,
                zipcode, latitude, longitude
            FROM persons_virtual_table
            ON CONFLICT DO UPDATE SET 
                        domain = EXCLUDED.domain,
                        age_group = EXCLUDED.age_group,
                        city = EXCLUDED.city,
                        country = EXCLUDED.country,
                        country_code = EXCLUDED.country_code,
                        street = EXCLUDED.street,
                        street_name = EXCLUDED.street_name,
                        building_number = EXCLUDED.building_number,
                        zipcode = EXCLUDED.zipcode,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        updated_at = EXCLUDED.updated_at
        """)
        
        return len(records)
    
    def get_german_gmail_users(self) -> float:
        """
        Calculate the percentage of Gmail users among all users in Germany.
        
        Returns:
            float: The percentage of Gmail users in Germany, rounded to 2 decimal places.
                Returns 0.0 if no users are found in Germany.
        """
        result = self.conn.execute("""
            SELECT
                ROUND((COUNT(CASE WHEN domain = 'gmail.com' THEN 1 END) * 100.0 /
                COUNT(*)), 2) AS percentage_germany_gmail
            FROM persons
            WHERE country = 'Germany'
        """).fetchone()
        
        return result[0]
    
    def get_top_three_gmail_users(self) -> List[Tuple]:
        """
        Get the top 3 countries with the highest number of Gmail users.
        Uses DENSE_RANK to handle ties properly (countries with the same
        count will have the same rank).
        
        Returns:
            List[Tuple]: A list of tuples containing (country_name, gmail_user_count)
                    for the top 3 countries. The list is ordered by Gmail user
                    count in descending order."""
        result = self.conn.execute("""
            SELECT
                country
            , COUNT(*) AS gmail_users
            FROM persons
            WHERE domain = 'gmail.com'
            GROUP BY country
            QUALIFY DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) <= 3
        """).fetchall()
        
        return result
    
    def get_gmail_users_over_sixty(self) -> int:
        """
        Count the number of Gmail users who are over 60 years old.
        
        Note: The method assumes age_group is formatted as '[min-max]' and uses
        1-based indexing to extract the upper bound after splitting on '-'.
        
        Returns:
            int: The total count of Gmail users over 60 years old.
            
        Raises:
            May raise database or parsing errors if age_group format is unexpected.
        """
        result = self.conn.execute("""
            SELECT
                COUNT(*)
            FROM persons
            WHERE domain = 'gmail.com'
            -- We get the upper bound of the age_group. 1-based indexing. 
            AND CAST(REPLACE(SPLIT(age_group, '-')[2], ']', '') AS INT) > 60
        """).fetchone()
                
        return result[0]
