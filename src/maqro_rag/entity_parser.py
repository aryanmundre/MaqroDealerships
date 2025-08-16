"""
Entity parser for extracting structured vehicle and customer signals from user messages.
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class VehicleQuery:
    """Structured vehicle query extracted from user message."""
    make: Optional[str] = None
    model: Optional[str] = None
    trim: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    color: Optional[str] = None
    budget_max: Optional[float] = None
    body_type: Optional[str] = None
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
    
    @property
    def has_strong_signals(self) -> bool:
        """Check if query has strong enough signals for filtering."""
        return any([
            self.make, self.model, self.year_min, self.year_max,
            self.budget_max, self.body_type
        ])


class EntityParser:
    """Parser for extracting vehicle and customer entities from text."""
    
    def __init__(self):
        """Initialize entity parser with synonym mappings."""
        self.make_synonyms = {
            'vw': 'volkswagen', 'volkswagen': 'volkswagen',
            'bmw': 'bmw', 'mercedes': 'mercedes-benz', 'benz': 'mercedes-benz',
            'toyota': 'toyota', 'honda': 'honda', 'nissan': 'nissan',
            'ford': 'ford', 'chevrolet': 'chevrolet', 'chevy': 'chevrolet',
            'hyundai': 'hyundai', 'kia': 'kia', 'mazda': 'mazda',
            'subaru': 'subaru', 'jeep': 'jeep', 'dodge': 'dodge',
            'chrysler': 'chrysler', 'audi': 'audi', 'lexus': 'lexus',
            'acura': 'acura', 'infiniti': 'infiniti', 'buick': 'buick',
            'cadillac': 'cadillac', 'lincoln': 'lincoln', 'volvo': 'volvo',
            'mini': 'mini', 'fiat': 'fiat', 'alfa': 'alfa romeo',
            'porsche': 'porsche', 'jaguar': 'jaguar', 'land rover': 'land rover',
            'range rover': 'land rover', 'maserati': 'maserati', 'ferrari': 'ferrari',
            'lamborghini': 'lamborghini', 'bentley': 'bentley', 'rolls': 'rolls royce',
            'rolls royce': 'rolls royce', 'aston': 'aston martin', 'aston martin': 'aston martin'
        }
        
        self.body_type_synonyms = {
            'sedan': 'sedan', 'car': 'sedan', 'suv': 'suv', 'truck': 'truck',
            'pickup': 'truck', 'hatchback': 'hatchback', 'wagon': 'wagon',
            'convertible': 'convertible', 'coupe': 'coupe', 'minivan': 'minivan',
            'van': 'minivan', 'crossover': 'suv', 'compact': 'sedan',
            'midsize': 'sedan', 'fullsize': 'sedan', 'luxury': 'sedan'
        }
        
        self.color_synonyms = {
            'white': 'white', 'black': 'black', 'red': 'red', 'blue': 'blue',
            'silver': 'silver', 'gray': 'gray', 'grey': 'gray', 'green': 'green',
            'yellow': 'yellow', 'orange': 'orange', 'purple': 'purple',
            'brown': 'brown', 'tan': 'tan', 'beige': 'beige', 'gold': 'gold',
            'navy': 'blue', 'dark blue': 'blue', 'light blue': 'blue',
            'dark red': 'red', 'light red': 'red', 'dark green': 'green',
            'light green': 'green', 'dark gray': 'gray', 'light gray': 'gray'
        }
    
    def parse_message(self, message: str) -> VehicleQuery:
        """Parse user message to extract vehicle query entities."""
        message_lower = message.lower().strip()
        
        # Extract make and model
        make, model, trim = self._extract_make_model_trim(message_lower)
        
        # Extract year range
        year_min, year_max = self._extract_year_range(message_lower)
        
        # Extract color
        color = self._extract_color(message_lower)
        
        # Extract budget
        budget_max = self._extract_budget(message_lower)
        
        # Extract body type
        body_type = self._extract_body_type(message_lower)
        
        # Extract features
        features = self._extract_features(message_lower)
        
        return VehicleQuery(
            make=make,
            model=model,
            trim=trim,
            year_min=year_min,
            year_max=year_max,
            color=color,
            budget_max=budget_max,
            body_type=body_type,
            features=features
        )
    
    def _extract_make_model_trim(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract make, model, and trim from text."""
        
        # Model to make mapping
        model_to_make = {
            # Toyota models
            'camry': 'toyota', 'corolla': 'toyota', 'rav4': 'toyota', 'highlander': 'toyota',
            'tacoma': 'toyota', 'tundra': 'toyota', 'prius': 'toyota', 'sienna': 'toyota',
            'avalon': 'toyota', 'yaris': 'toyota', 'venza': 'toyota', '4runner': 'toyota',
            'sequoia': 'toyota', 'land cruiser': 'toyota',
            
            # Honda models
            'civic': 'honda', 'accord': 'honda', 'cr-v': 'honda', 'pilot': 'honda',
            'odyssey': 'honda', 'ridgeline': 'honda', 'fit': 'honda', 'insight': 'honda',
            'passport': 'honda', 'hr-v': 'honda', 'element': 'honda',
            
            # Nissan models
            'altima': 'nissan', 'sentra': 'nissan', 'rogue': 'nissan', 'murano': 'nissan',
            'pathfinder': 'nissan', 'frontier': 'nissan', 'titan': 'nissan', 'versa': 'nissan',
            'maxima': 'nissan', 'armada': 'nissan', 'quest': 'nissan',
            
            # Ford models
            'f-150': 'ford', 'f-250': 'ford', 'f-350': 'ford', 'mustang': 'ford',
            'escape': 'ford', 'explorer': 'ford', 'edge': 'ford', 'expedition': 'ford',
            'ranger': 'ford', 'bronco': 'ford', 'maverick': 'ford',
            
            # Chevrolet models
            'silverado': 'chevrolet', 'tahoe': 'chevrolet', 'suburban': 'chevrolet',
            'equinox': 'chevrolet', 'traverse': 'chevrolet', 'malibu': 'chevrolet',
            'impala': 'chevrolet', 'camaro': 'chevrolet', 'corvette': 'chevrolet',
            'colorado': 'chevrolet', 'bolt': 'chevrolet',
            
            # Hyundai models
            'tucson': 'hyundai', 'santa fe': 'hyundai', 'palisade': 'hyundai',
            'elantra': 'hyundai', 'sonata': 'hyundai', 'accent': 'hyundai',
            'veloster': 'hyundai', 'kona': 'hyundai', 'ioniq': 'hyundai', 'nexo': 'hyundai',
            
            # Kia models
            'sportage': 'kia', 'sorento': 'kia', 'telluride': 'kia', 'forte': 'kia',
            'rio': 'kia', 'soul': 'kia', 'stinger': 'kia', 'k5': 'kia', 'niro': 'kia', 'ev6': 'kia',
            
            # Mazda models
            'cx-5': 'mazda', 'cx-9': 'mazda', 'mazda3': 'mazda', 'mazda6': 'mazda',
            'mx-5': 'mazda', 'miata': 'mazda', 'cx-30': 'mazda', 'cx-50': 'mazda', 'mx-30': 'mazda',
            
            # Subaru models
            'outback': 'subaru', 'forester': 'subaru', 'crosstrek': 'subaru',
            'impreza': 'subaru', 'legacy': 'subaru', 'wrx': 'subaru', 'brz': 'subaru', 'ascent': 'subaru',
            
            # Jeep models
            'wrangler': 'jeep', 'grand cherokee': 'jeep', 'cherokee': 'jeep',
            'compass': 'jeep', 'renegade': 'jeep', 'gladiator': 'jeep', 'commander': 'jeep',
            
            # Dodge models
            'challenger': 'dodge', 'charger': 'dodge', 'durango': 'dodge',
            'journey': 'dodge', 'avenger': 'dodge', 'caliber': 'dodge', 'neon': 'dodge', 'stratus': 'dodge',
            
            # Chrysler models
            '300': 'chrysler', '200': 'chrysler', 'pacifica': 'chrysler', 'voyager': 'chrysler',
            'pt cruiser': 'chrysler', 'sebring': 'chrysler', 'concorde': 'chrysler', 'intrepid': 'chrysler',
            
            # Audi models
            'a3': 'audi', 'a4': 'audi', 'a6': 'audi', 'a8': 'audi', 'q3': 'audi',
            'q5': 'audi', 'q7': 'audi', 'q8': 'audi', 'tt': 'audi', 'rs': 'audi',
            's3': 'audi', 's4': 'audi', 's6': 'audi', 's8': 'audi',
            
            # BMW models
            '3 series': 'bmw', '5 series': 'bmw', '7 series': 'bmw', 'x1': 'bmw',
            'x3': 'bmw', 'x5': 'bmw', 'x7': 'bmw', 'z4': 'bmw', 'm3': 'bmw', 'm5': 'bmw', 'm8': 'bmw',
            
            # Mercedes models
            'c-class': 'mercedes-benz', 'e-class': 'mercedes-benz', 's-class': 'mercedes-benz',
            'gla': 'mercedes-benz', 'glb': 'mercedes-benz', 'glc': 'mercedes-benz',
            'gle': 'mercedes-benz', 'gls': 'mercedes-benz', 'a-class': 'mercedes-benz',
            'cla': 'mercedes-benz', 'cls': 'mercedes-benz',
            
            # Lexus models
            'es': 'lexus', 'ls': 'lexus', 'gs': 'lexus', 'is': 'lexus', 'rc': 'lexus',
            'lc': 'lexus', 'nx': 'lexus', 'rx': 'lexus', 'gx': 'lexus', 'lx': 'lexus',
            'ux': 'lexus', 'rz': 'lexus', 'lfa': 'lexus',
            
            # Acura models
            'tl': 'acura', 'tsx': 'acura', 'rl': 'acura', 'mdx': 'acura', 'rdx': 'acura',
            'ilx': 'acura', 'nsx': 'acura', 'integra': 'acura', 'legend': 'acura', 'vigor': 'acura',
            
            # Infiniti models
            'q50': 'infiniti', 'q60': 'infiniti', 'qx50': 'infiniti', 'qx60': 'infiniti',
            'qx80': 'infiniti', 'g37': 'infiniti', 'm37': 'infiniti', 'm56': 'infiniti',
            'fx35': 'infiniti', 'fx45': 'infiniti', 'ex35': 'infiniti', 'ex37': 'infiniti',
            
            # Buick models
            'encore': 'buick', 'enclave': 'buick', 'envision': 'buick', 'lacrosse': 'buick',
            'regal': 'buick', 'verano': 'buick', 'cascada': 'buick',
            
            # Cadillac models
            'cts': 'cadillac', 'ats': 'cadillac', 'xts': 'cadillac', 'xt5': 'cadillac',
            'xt6': 'cadillac', 'escalade': 'cadillac', 'escalade esv': 'cadillac',
            'ct6': 'cadillac', 'ct4': 'cadillac', 'ct5': 'cadillac',
            
            # Lincoln models
            'mkz': 'lincoln', 'mkc': 'lincoln', 'mkx': 'lincoln', 'mkt': 'lincoln',
            'navigator': 'lincoln', 'continental': 'lincoln', 'aviator': 'lincoln',
            'corsair': 'lincoln', 'nautilus': 'lincoln',
            
            # Volvo models
            's60': 'volvo', 's80': 'volvo', 's90': 'volvo', 'v60': 'volvo', 'v90': 'volvo',
            'xc40': 'volvo', 'xc60': 'volvo', 'xc90': 'volvo', 'c30': 'volvo', 'c70': 'volvo',
            's40': 'volvo', 'v50': 'volvo',
            
            # Mini models
            'cooper': 'mini', 'countryman': 'mini', 'clubman': 'mini',
            'convertible': 'mini', 'hardtop': 'mini', 'roadster': 'mini',
            
            # Fiat models
            '500': 'fiat', '500l': 'fiat', '500x': 'fiat', '124 spider': 'fiat',
            '500c': 'fiat', '500e': 'fiat',
            
            # Alfa Romeo models
            'giulia': 'alfa romeo', 'stelvio': 'alfa romeo', 'tonale': 'alfa romeo',
            '4c': 'alfa romeo', 'giulietta': 'alfa romeo', 'mito': 'alfa romeo',
            'brera': 'alfa romeo', 'spider': 'alfa romeo',
            
            # Porsche models
            '911': 'porsche', 'cayenne': 'porsche', 'macan': 'porsche', 'panamera': 'porsche',
            'cayman': 'porsche', 'boxster': 'porsche', 'taycan': 'porsche', 'carrera': 'porsche',
            
            # Jaguar models
            'xe': 'jaguar', 'xf': 'jaguar', 'xj': 'jaguar', 'f-type': 'jaguar',
            'f-pace': 'jaguar', 'e-pace': 'jaguar', 'i-pace': 'jaguar',
            'xjr': 'jaguar', 'xjl': 'jaguar',
            
            # Land Rover models
            'discovery': 'land rover', 'defender': 'land rover', 'range rover': 'land rover',
            'range rover sport': 'land rover', 'range rover evoque': 'land rover',
            'range rover velar': 'land rover',
            
            # Maserati models
            'ghibli': 'maserati', 'quattroporte': 'maserati', 'levante': 'maserati',
            'grecale': 'maserati', 'mc20': 'maserati', 'granturismo': 'maserati',
            'granturismo sport': 'maserati',
            
            # Ferrari models
            '488': 'ferrari', 'f8': 'ferrari', '812': 'ferrari', 'sf90': 'ferrari',
            'roma': 'ferrari', 'portofino': 'ferrari', 'monza': 'ferrari',
            'laferrari': 'ferrari', 'enzo': 'ferrari', 'f40': 'ferrari', 'f50': 'ferrari',
            
            # Lamborghini models
            'huracan': 'lamborghini', 'aventador': 'lamborghini', 'urus': 'lamborghini',
            'gallardo': 'lamborghini', 'murcielago': 'lamborghini', 'diablo': 'lamborghini',
            'countach': 'lamborghini', 'reventon': 'lamborghini',
            
            # Bentley models
            'continental': 'bentley', 'flying spur': 'bentley', 'bentayga': 'bentley',
            'arnage': 'bentley', 'brooklands': 'bentley', 'azure': 'bentley', 'turbo r': 'bentley',
            
            # Rolls Royce models
            'phantom': 'rolls royce', 'ghost': 'rolls royce', 'wraith': 'rolls royce',
            'dawn': 'rolls royce', 'cullinan': 'rolls royce', 'silver shadow': 'rolls royce',
            'silver spur': 'rolls royce', 'corniche': 'rolls royce',
            
            # Aston Martin models
            'db11': 'aston martin', 'dbx': 'aston martin', 'vantage': 'aston martin',
            'dbs': 'aston martin', 'rapide': 'aston martin', 'virage': 'aston martin',
            'vanquish': 'aston martin', 'one-77': 'aston martin', 'cygnet': 'aston martin',
            
            # Volkswagen models
            'tiguan': 'volkswagen', 'atlas': 'volkswagen', 'golf': 'volkswagen',
            'jetta': 'volkswagen', 'passat': 'volkswagen', 'arteon': 'volkswagen',
            'id.4': 'volkswagen', 'taos': 'volkswagen', 'touareg': 'volkswagen', 'e-golf': 'volkswagen'
        }
        
        make = None
        model = None
        trim = None
        
        # Check for make synonyms first with word boundaries
        # Sort by length (longest first) to prioritize longer matches like "land rover" over "land"
        sorted_makes = sorted(self.make_synonyms.items(), key=lambda x: len(x[0]), reverse=True)
        for synonym, canonical in sorted_makes:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(synonym) + r'\b', text):
                make = canonical
                break
        
        # Look for model patterns and infer make if not already found
        # Sort by length (longest first) to avoid partial matches
        sorted_models = sorted(model_to_make.items(), key=lambda x: len(x[0]), reverse=True)
        for model_name, model_make in sorted_models:
            # Use word boundaries to avoid partial matches like "rs" in "Porsche"
            if re.search(r'\b' + re.escape(model_name) + r'\b', text):
                model = model_name
                if not make:  # Only set make if not already found
                    make = model_make
                break
        
        # Extract trim (common trims)
        trim_patterns = [
            r'\b(se|s|ex|lx|sport|touring|premium|luxury|platinum|limited|elite|advance|reserve|signature|grand touring|gt|turbo|hybrid|ev|electric|plug-in|phev)\b'
        ]
        
        for pattern in trim_patterns:
            match = re.search(pattern, text)
            if match:
                trim = match.group(1)
                break
        
        return make, model, trim
    
    def _extract_year_range(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract year range from text."""
        # Year range: "2021-2023", "2021 to 2023" (check this first)
        year_range = re.search(r'\b(20[12]\d)\s*[-–—to]\s*(20[12]\d)\b', text)
        if year_range:
            year_min = int(year_range.group(1))
            year_max = int(year_range.group(2))
            return year_min, year_max
        
        # Single year: "2021", "2021 model"
        single_year = re.search(r'\b(20[12]\d)\b', text)
        if single_year:
            year = int(single_year.group(1))
            return year, year
        
        return None, None
    
    def _extract_color(self, text: str) -> Optional[str]:
        """Extract color from text."""
        for synonym, canonical in self.color_synonyms.items():
            if synonym in text:
                return canonical
        return None
    
    def _extract_budget(self, text: str) -> Optional[float]:
        """Extract budget from text."""
        # Patterns: "under 32k", "under $32k", "under 32,000", "under $32,000"
        budget_patterns = [
            r'under\s*\$?(\d+(?:,\d{3})*)\s*k',
            r'under\s*\$?(\d+(?:,\d{3})*)\s*thousand',
            r'under\s*\$?(\d+(?:,\d{3})*)\s*000',
            r'under\s*\$?(\d+(?:,\d{3})*)',
            r'less\s+than\s*\$?(\d+(?:,\d{3})*)\s*k',
            r'less\s+than\s*\$?(\d+(?:,\d{3})*)\s*thousand',
            r'less\s+than\s*\$?(\d+(?:,\d{3})*)\s*000',
            r'less\s+than\s*\$?(\d+(?:,\d{3})*)',
            r'around\s*\$?(\d+(?:,\d{3})*)\s*k',
            r'around\s*\$?(\d+(?:,\d{3})*)\s*thousand',
            r'around\s*\$?(\d+(?:,\d{3})*)\s*000',
            r'around\s*\$?(\d+(?:,\d{3})*)',
            r'budget\s*\$?(\d+(?:,\d{3})*)\s*k',
            r'budget\s*\$?(\d+(?:,\d{3})*)\s*thousand',
            r'budget\s*\$?(\d+(?:,\d{3})*)\s*000',
            r'budget\s*\$?(\d+(?:,\d{3})*)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str)
                
                # Convert k/thousand to full amount
                if 'k' in pattern or 'thousand' in pattern:
                    amount *= 1000
                elif '000' in pattern:
                    amount *= 1000
                
                return amount
        
        return None
    
    def _extract_body_type(self, text: str) -> Optional[str]:
        """Extract body type from text."""
        for synonym, canonical in self.body_type_synonyms.items():
            if synonym in text:
                return canonical
        return None
    
    def _extract_features(self, text: str) -> List[str]:
        """Extract vehicle features from text."""
        features = []
        
        feature_patterns = [
            r'\b(3rd row|third row|third-row)\b',
            r'\b(hybrid|electric|ev|phev|plug-in)\b',
            r'\b(awd|4wd|all wheel drive|four wheel drive)\b',
            r'\b(leather|heated seats|ventilated seats|cooled seats)\b',
            r'\b(navigation|nav|gps)\b',
            r'\b(sunroof|moonroof|panoramic)\b',
            r'\b(backup camera|rear camera|360 camera)\b',
            r'\b(blind spot|blind spot monitoring|bsm)\b',
            r'\b(lane departure|lane keeping|lane assist)\b',
            r'\b(adaptive cruise|radar cruise|smart cruise)\b',
            r'\b(apple carplay|android auto|carplay)\b',
            r'\b(bluetooth|bluetooth audio|wireless)\b',
            r'\b(premium audio|bose|harman kardon|jbl)\b',
            r'\b(remote start|push button start|keyless)\b',
            r'\b(automatic|manual|cvt|transmission)\b'
        ]
        
        for pattern in feature_patterns:
            match = re.search(pattern, text)
            if match:
                features.append(match.group(1))
        
        return features 