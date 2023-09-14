# The-Issue-Is-Backend

This is the backend for the 'The-Issue-Is' project. This is a Python Flask application that uses MindsDB to generate high-quality GitHub issues. The API has been containerized using Docker.

## Run Locally

Clone the project

```bash
  git clone https://github.com/The-Issue-Is/the-issue-is-backend.git
```

Go to the project directory

```bash
  cd the-issue-is-backend
```

Build the Docker image

```bash
  docker build -t the-issue-is-backend .
```

Start the server

```bash
  docker run -p 4000:4000 the-issue-is-backend
```

## API Reference


### Access Token
```http
POST /access_token
```
| Parameter | Type     | Description                                                   |
| :-------  | :------- | :------------------------------------------------------------ |
| `code`    | `string` | **Required**. The code to exchange for an access token.       |

This endpoint retrieves an access token using a provided code. The code should be passed in the request body.

#### Login
    
```http
POST /login
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `login`   | `string` | **Required**. Your MindsDB login/username |
| `password`| `string` | **Required**. Your MindsDB password |

Ths request will login to your MindsDB account and generate a JWT token that will be used to authenticate all other requests.

You can get your MindsDB login/username and password by signing up at [MindsDB](https://cloud.mindsdb.com/).

#### Databases

```http
PUT /databases
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `database_name`   | `string` | **Required**. The name of the database you want to create |
| `repository`| `string` | **Required**. The GitHub repository you want to connect to |
| `api_key`| `string` | **Required**. A GitHub API key |

This request will create a new database in your MindsDB account and connect it to the GitHub repository you specified. 

```http
GET /databases
```
This request will return a list of all the databases you have created in your MindsDB account.

#### Models

```http
PUT /models
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `project_name`   | `string` | **Required**. The name of the MindsDB project you want to create the model in |
| `model_name`| `string` | **Required**. The name of the model you want to create |

This request will create a new model in the specified MindsDB project.

The PROMPT_TEMPLATE and MAX_TOKENS configurations are maintained as environment variables in the Docker container. These can be changed by editing the Dockerfile.

```http
GET /models
```

| Query Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `project_name`   | `string` | **Required**. The name of the MindsDB project you want to list the models in |

This request will return a list of all the models you have created in your MindsDB account.

#### Issues

```http
PUT /issues
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `database_name`   | `string` | **Required**. The name of the database you want to create the issue in |
| `title`| `string` | **Required**. The title of the issue you want to create |
| `description`| `string` | **Required**. The description of the issue you want to create |

This request will create a new issue in the specified GitHub repository via the MindsDB database you specified.

```http
POST /issues/description
``` 

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `project_name`   | `string` | **Required**. The name of the MindsDB project that the model you want to use is in |
| `model_name`| `string` | **Required**. The name of the model you want to use |
| `title`| `string` | **Required**. The title of the issue you want to generate a description for |
| `description`| `string` | **Required**. The description of the issue you want to improve on |
| `sections`| `string` | **Required**. The sections you want to generate in the description for the issue |
| `style`| `string` | **Required**. The style you want to use to generate the description for the issue |

