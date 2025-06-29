import requests
import yaml
import os
from logger import logger
from time import sleep
from data_model import Person
from pydantic import ValidationError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from typing import List, Dict, Any, Generator
from exceptions import DataQualityError

with open('./fakerapi/config.yaml', 'r') as f:
    CONFIG = yaml.safe_load(f)

class API:
    def __init__(self):
        self.session = requests.Session()
        self.endpoints = CONFIG.get('endpoints', [])
        self.target_endpoint = os.getenv('ENDPOINT')
        self.timeout = CONFIG.get('timeout', 10)
        self.total_records_needed = CONFIG.get('total_records_needed', 30000)
        self.db_batch_size = CONFIG.get('db_batch_size', 30000)

    def _get_endpoint_config(self) -> Dict[str, Any]:
        """
        Retrieve the configuration for the target endpoint.
        
        Searches through the list of available endpoint configurations to find
        the one matching the target endpoint name specified in self.target_endpoint.
        
        Returns:
            Dict[str, Any]: The configuration dictionary for the target endpoint,
                            containing all endpoint-specific settings and parameters.
        
        Raises:
            ValueError: If the target endpoint is not found in the available
                        endpoint configurations.
        """
        for endpoint_config in self.endpoints:
            if endpoint_config['name'] == self.target_endpoint:
                return endpoint_config
        raise ValueError(f"Endpoint {self.target_endpoint} not found")
    
    def _validate_data_quality(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate data quality using Pydantic models.
        
        Args:
            records: Raw records from API
            
        Returns:
            Validated and cleaned records
            
        Raises:
            DataQualityError: If data quality issues are found
        """
        validated_records = []
        invalid_count = 0
        
        for record in records:
            try:
                # Validate using Pydantic model
                person = Person(**record)
                validated_records.append(person.model_dump())

            except ValidationError as e:
                invalid_count += 1
                logger.warning(f"Invalid record found: {e}")
                continue

        # Check if too many records are invalid (>5%)
        if invalid_count > len(records) * 0.05:
            raise DataQualityError(
                f"Too many invalid records: {invalid_count}/{len(records)}"
            )
        
        logger.info(
            f"Data validation complete. Valid: {len(validated_records)}, "
            f"Invalid: {invalid_count}"
        )
        
        return validated_records
    
    @retry(
        retry=retry_if_exception_type((requests.exceptions.RequestException,)),
        wait=wait_exponential(multiplier=CONFIG.get('backoff_factor')),
        stop=stop_after_attempt(CONFIG.get('max_retries')),
        reraise=True
    )
    def _fetch_batch(self, endpoint: str) -> List[Dict[str, Any]]:
        """
        Fetch a batch of data from the API with automatic retry logic.
        
        Args:
            endpoint (str): The API endpoint path to append to the base URL.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the batch data
                                from the 'data' field of the API response.
        
        Raises:
            requests.exceptions.HTTPError: When the API returns an HTTP error status
                                        or when the response format is unexpected.
            requests.exceptions.RequestException: For network-related errors after
                                                all retry attempts are exhausted.
        
        Retry Behavior:
            - Retries only on requests.exceptions.RequestException
            - Uses exponential backoff with configurable multiplier via CONFIG['backoff_factor']
            - Maximum retry attempts configured via CONFIG['max_retries']
            - Re-raises the final exception if all retries fail
        """
        try:
            response = self.session.get(
                url=f"{CONFIG.get('api_base_url')}{endpoint}",
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            if 'data' in data:
                return data['data']
            else: 
                logger.error(f'Unexpected response format: {data}')
                raise requests.exceptions.HTTPError
            
        except requests.exceptions.HTTPError as e:
            logger.error(f'Error fetching batch: {e}')
            raise e
    
    def fetch_all_data(self) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Fetch all required data records from the API in batches with validation.
    
        This method retrieves data from the configured API endpoint in batches, validates
        each batch for data quality, and yields the results. It continues fetching until
        the total number of records specified in CONFIG['total_records_needed'] is reached.
        
        The method implements:
        - Batch processing to handle large datasets efficiently
        - Data quality validation using Pydantic models
        - Rate limiting with small delays between requests
        - Pagination using a seed parameter
        - Error handling with retry logic for failed requests
        - Progress logging
        
        Yields:
            List[Dict[str, Any]]: A batch of raw records from the API. Note that
                these are the original records before validation, not the validated ones.
        
        Raises:
            DataQualityError: When data validation fails (propagated from _validate_data_quality)
        """
        endpoint_config = self._get_endpoint_config()
        self.session.params = endpoint_config.get('params')
        total_fetched = 0
        seed = 1

        while total_fetched < CONFIG.get('total_records_needed'):
            try:
                records = self._fetch_batch(endpoint=endpoint_config.get('url'))
                validated_records = self._validate_data_quality(records)

                total_fetched += len(validated_records)
                logger.info(f"Progress: {total_fetched}/{CONFIG.get('total_records_needed')}")

                yield validated_records

                # Small sleep to avoid avoid reaching the rate limit
                sleep(0.1)
                
                # Update pagination parameter for next batch
                seed += 1
                self.session.params.update({'_seed': seed})

            except (requests.exceptions.RequestException) as e:
                logger.error(f"Batch failed: {e}")
                continue
