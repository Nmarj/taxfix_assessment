import hashlib
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, computed_field

class Person(BaseModel):
    firstname:str = Field(exclude=True)
    lastname:str = Field(exclude=True)
    email: EmailStr = Field(exclude=True)
    birthday: str = Field(exclude=True)
    address: dict = Field(exclude=True)
    street: str = '****'
    street_name: str =  '****'
    building_number: str = '****'
    zipcode: str = '****'
    latitude: str = '****'
    longitude: str = '****'

    @computed_field
    @property
    def id(self) -> str:
        """
        Create id from firstname + lastname since ids are not unique 
        between seeds.
        """
        name_combo = f"{self.firstname.lower()}{self.lastname.lower()}"
        return hashlib.md5(name_combo.encode()).hexdigest()[:8]

    @computed_field
    @property
    def domain(self) -> str:
        return self.email.split('@')[-1]
    
    @computed_field
    @property
    def age_group(self) -> str:
        return self._calculate_age_group()
    
    @computed_field
    @property
    def city(self) -> str:
        return self.address['city']
    
    @computed_field
    @property
    def country(self) -> str:
        return self.address['country']
    
    @computed_field
    @property
    def country_code(self) -> str:
        return self.address['country_code']
    
    def _calculate_age_group(self):
        """
        Convert a birthdate to a 10-year age group.
        
        Args:
            birthdate: Can be a string or datetime object

        Returns:
            String in format "[X0-Y0]" representing age group
        """
        today = datetime.now()

        # Try common date formats
        for fmt in ['%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                birth_dt = datetime.strptime(self.birthday, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Could not parse date: {self.birthday}")

        # Calculate age
        age = today.year - birth_dt.year
        
        # Determine age group (10-year brackets)
        group_start = (age // 10) * 10
        group_end = group_start + 10
        
        return f"[{group_start}-{group_end}]"
