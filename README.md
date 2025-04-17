# STRATA-FIT Data Validation App

## Project Description
The STRATA-FIT Data Validation App is a FastAPI-based tool designed to validate CSV data files containing clinical information about patients with rheumatoid arthritis (RA). The validation is performed against a [customizable YAML schema](/config/schema.yaml), with support for pydantic constraints like `ge`, `le`, and [more](https://docs.pydantic.dev/latest/concepts/fields/#field-aliases:~:text=Alias%20concepts%20page.-,Numeric%20Constraints,Here%27s%20an%20example%3A,-from%20pydantic%20import), allowing users to enforce specific data quality and integrity rules.

The application supports file uploads through an API endpoint where users can submit their CSV files to be validated. Errors and discrepancies are reported back in a user-friendly format, making it easier for clinicians and researchers to identify and correct data issues.

## Diagrams
### Component Diagram
![app](docs/app.png)

## Usage Instructions

[![Watch the usage guide video](docs/loom-video-thumbnail.png)](https://www.loom.com/share/df44944e2711460a921164e201261044)

### Running the Application

#### Dockerized Application

Ensure you have a docker daemon installed. The easiest option is to download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/).

To run the application in a Docker container with custom configurations (`config/`):

1. **Pull the Docker Image**:
   ```bash
   docker pull ghcr.io/mdw-nl/strata-fit-data-val:latest
   ```

2. **Run the Docker Container**: 
    
    2.1. Using regular configuration:
    ```bash
    docker run --rm -p 8000:8000 ghcr.io/mdw-nl/strata-fit-data-val:latest
    ```

    2.2. Mount your custom configuration directory to the container:
    ```bash
    docker run --rm -p 8000:8000 -v $(pwd)/config:/app/config ghcr.io/mdw-nl/strata-fit-data-val:latest
    ```
    This command maps the local `config/` directory to `/app/config` within the container (with `-v $(pwd)/config:/app/config`), ensuring your custom settings are used.

3. **Access the Application**: Visit http://localhost:8000/docs to interact with the API.

#### Uploading Custom YAML Schema

To use your own data validation schema:

1. **Edit the `schema.yaml` File**: Modify the `config/schema.yaml` file with your custom data validation rules.

2. **Mount the Configuration Directory**: Ensure your modified `config/` directory is correctly mounted when running the Docker container:
    ```bash
    docker run --rm -p 8000:8000 -v $(pwd)/config:/app/config ghcr.io/mdw-nl/strata-fit-data-val:latest
    ```

3. **Check Your Schema**: You can verify the current schema by accessing the `/schema` endpoint at http://localhost:8000/docs or with the following command:
    ```bash
    curl http://localhost:8000/schema
    ```

#### Custom app settings

All runtime parameters live in `config/settings.yaml`, so you don’t need to touch code to adjust:
```yaml
app:
  data:
    chunksize: 10          # number of rows to process per pandas chunk
    model_name: PatientData
  errors:
    max_to_collect: 1000   # stop streaming after this many validation errors
```
- `app.data.chunksize` controls how many rows are read & validated at once (lower it to reduce memory use).
- `app.data.model_name` chooses which Pydantic model from config/schema.yaml to use.
- `app.errors.max_to_collect` caps the total number of error objects emitted to the client.

Update these values, then restart your container (or local server) and the /validate endpoint will immediately pick up the new limits—no code changes or redeploy required.

### Development Mode
For local development:

1. **Install Dependencies**: Ensure Python 3.10+ is installed, then install required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2. **Run the Application**: Start the FastAPI server with Uvicorn
    ```bash
    uvicorn api.main:app --reload
    ```

3. Interact with the API
    Access the API through a [web browser](http://localhost:8000) or use tools like curl or Postman to upload CSV files for validation:

    ```bash
    curl -F 'file=@path_to_your_file.csv' http://localhost:8000/validate
    ```

### API Endpoints

* `/validate`: Upload and validate your CSV file.
* `/settings`: Access the current application settings.
* `/schema`: Access the current data schema.

## Additional Resources
For more detailed development guidelines, please refer to the [DEV.md](DEV.md) file.