import os

class DataSink:
    def save(self, data, filename, metadata):
        """Save data with metadata."""
        raise NotImplementedError("Must be implemented by subclasses.")
    
class LocalFileDataSink(DataSink):
    def __init__(self, directory):
        self.directory = directory
    
    def save(self, data, filename, metadata):
        with open(os.path.join(self.directory, filename), 'w') as file:
            file.write(data)
        # Add logic here to save metadata if needed

class S3DataSink(DataSink):
    # Add initialization with S3 credentials and bucket info
    def save(self, data, filename, metadata):
        # Implement logic to save data to S3 bucket here
        pass

class CyberduckDataSink(DataSink):
    # Add initialization with Cyberduck credentials and config
    def save(self, data, filename, metadata):
        # Implement logic to save data to Cyberduck storage here
        pass