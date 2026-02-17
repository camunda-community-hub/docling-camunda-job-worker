## Python-based Job Worker for Camunda 8 that uses Docling to convert PDF or Excel files to Markdown and HTML
This is a work in progress, it aims to help make sense of large PDF files and allow their content to be used in agentic processes

### Preparation and Installation
In order to run this project on your machine you will need to follow the installation instructions from [docling](https://github.com/docling-project/docling) 

#### Dependencies
I tested this project on a macbook with python3.13, it did not fly with python3.12 due to missing mps features for docling.

These installed prerequisits should keep you covered.
`pip install docling grpcio grpcio-tools`

and prefetch the models: [advanced options](https://docling-project.github.io/docling/usage/advanced_options/)

```
$ docling-tools models download
Downloading layout model...
Downloading tableformer model...
Downloading picture classifier model...
Downloading code formula model...
Downloading easyocr models...
Models downloaded into $HOME/.cache/docling/models.
```

#### Configure environment variables
Copy the included template and fill in your Camunda API credentials:
```
cp .env.template .env
```
Then edit the `.env` file and set your `client_id`, `client_secret`, `cluster_id` and `region`.

The template includes presets for both **SaaS** and **Self-Managed** mode — uncomment the section that matches your setup.

#### Import Connector Template
find the included ./CamundaConnectorTempate/Docling Converter.json and upload and publish it to a Camunda Modeler Webproject

### Quick Start with Make
Instead of running the steps above manually, you can simply run:
```
make
```
This will create a Python virtual environment, install dependencies, download Docling models, and start the worker. On first run it will also create a `.env` file from the template and remind you to fill in your credentials.

### Usage
Start up the worker by simply running it via python:
`python worker.py`

The worker will print:
```
starting docling worker...
opened channel
activating jobs of type converter.docling...
```
and then wait for incoming jobs — this is normal. It runs as a long-lived process and will process jobs as they arrive from Camunda.

Now you can create a Process, attach a start form with a file picker and point it to a variable name 'document' and add a task with the Docling Converter connector. Deploy the process and start it via Camunda Tasklist, upload a pdf file and see how Docling converts it for you. 

### additional thoughts
Keep in mind that this project is a work in progress and mainly aims to be a proof of concept, I'll try to find more time for refinement of it.
