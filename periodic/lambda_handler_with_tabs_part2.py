# Reserve keywords for special cases, including single and 3-letter symbols
reserved_symbols = {
  "Mx"  : "Apache MXNet on AWS", 
  "Tf"  : "TensorFlow on AWS", 
  "Eks" : "Elastic Container Service for Kubernetes", 
  "Ecs" : "Elastic Container Service", 
  "Db"  : "DocumentDB", 
  "53"  : "Route 53", 
  "X"   : "X-Ray", 
  "Ami" : "Deep Learning AMIs", 
  "Phd" : "Personal Health Dashboard", 
  "Cs"  : "CloudSearch", 
  "L"   : "Lambda", 
  "S3"  : "Simple Storage Service", 
  "A"   : "Athena", 
  "Vpc" : "VPC", 
  "Ec2" : "EC2", 
  "C9"  : "Cloud9", 
  "Gt"  : "SageMaker Ground Truth", 
  "Sns" : "Simple Notification Service", 
  "Sqs" : "Simple Queue Service", 
  "Hsm" : "CloudHSM", 
  "Ebs" : "Elastic Block Store", 
  "Cli" : "Command Line Interface", 
  "Cf"  : "CloudFront", 
  "Cm"  : "Cloud Map", 
  "Gl"  : "S3 Glacier", 
  "Sdk" : "Tools and SDKs", 
  "Lx"  : "Lex", 
  "M"   : "Macie", 
  "K"   : "Managed Streaming for Kafka", 
  "Emr" : "EMR", 
  "F"   : "Fargate"
}

# For reverse lookup  
reserved_services = dict(map(reversed, reserved_symbols.items()))

# Some names are just to long to display, shorten them here
preferred_names = {
  "Elastic Container Service for Kubernetes": "ECS for Kubernetes", 
  "Serverless Application Repository":"Serverless App Repo" 
}

# Default colors
colors = ["#834187", "#878541", "#458741", "#874145", 
          "#c92d39", "#3ac92d", "#2d44c9", "#c9762d", 
          "#ef8d22", "#2c22ef", "#ef22e5", "#e5ef22", 
          "#fcc438", "#8d38fc", "#fc38a7", "#a7fc38", 
          "#7ab648", "#b6487a", "#b66548", "#48adb6", 
          "#3aa6dd", "#dd703a", "#ddc23a", "#a73add"]

# Parse prefix and name
def parse_name(name):
    search = re.search( r"(AWS|Amazon)*\s*(.*)", name )
    prefix = search.group(1) or 'AWS'
    name = search.group(2)
    name = name.split("(",2)[0].strip()
    return prefix, name

# Create a symbol, roughly:
# 1. Use a pre-defined symbol
# 2. Create a 2 letter symbol using first letters of words in name
# 3. Create a 2 letter symbol using fallback sequence if needed (handles 1-letter names)
def create_symbol(symbols, name):
    symbol = ""
    if name in reserved_services:
      # We have a specific symbol to use for this service
      symbol = reserved_services[name]
      symbols[symbol] = name
    else:
      cleaned = re.sub(r"[&,-/.]","",name)
      words = cleaned.split(' ')
      words = [ elem for elem in words if not elem.islower() ]

      # Build candidate character pool from words
      initials = [ w[0:1] for w in words if w ]
      tails = [ w[1:] for w in words if len(w) > 1 ]
      chars = "".join(initials + tails)

      # Primary strategy: combine first char with following chars from pool
      for idx, first in enumerate(chars):
        first_up = first.upper()
        # prefer combining with subsequent chars
        for char in chars[idx+1:]:
          candidate = first_up + char.lower()
          if candidate not in symbols:
            symbols[candidate] = name
            reserved_services[name] = candidate
            symbol = candidate
            break
        if symbol:
          break

      # Fallback for very short names, e.g., "Q": allow single-letter or synthesize pairs
      if not symbol and chars:
        first_up = chars[0].upper()
        # Try single-letter if free
        if first_up not in symbols:
          symbols[first_up] = name
          reserved_services[name] = first_up
          symbol = first_up
        else:
          # Try first letter + a fallback sequence
          for suf in list('abcdefghijklmnopqrstuvwxyz') + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + ['1','2','3']:
            candidate = first_up + suf
            if candidate not in symbols:
              symbols[candidate] = name
              reserved_services[name] = candidate
              symbol = candidate
              break

    if not symbol:
      print("Couldn't generate symbol for %s: %s" % (name, chars if 'chars' in locals() else name))

    return symbol

# Funktion zum Sammeln von Daten aus der Directory API
def get_data_from_directory():
    periodic = {'categories': [], 'title': "Periodic Table of Amazon Web Services (Directory API)",
              'description': "AWS Services from Directory API"}
    
    # Symbols already used
    symbols = {}
    
    # Services already processed
    names = {}
    
    # Use AWS Products Directory endpoint to get services/features
    try:
        dj = get(AWS_PRODUCTS_API, headers=HEADERS, timeout=20)
        dj.raise_for_status()
        data = dj.json()
    except Exception as e:
        print("Failed to fetch directory API: %s" % e)
        data = {"items": []}
    items = data.get('items', [])