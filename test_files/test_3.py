#Import libraries

#Function to load credentials 
def load_credentials(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            endpoint = lines[0].split('=')[1].strip().strip('"')
            key = lines[0].split('=')[1].strip().strip('"')
        return endpoint, key
    except Exception as e:
        raise Exception(f"Error reading credentials from file: {e}")
    