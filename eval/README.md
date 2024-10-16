# RAG Evaluation (Deepeval)

## Introduction

Deepeval is used to perform the evaluation for RAG (Retrieval-Augmented Generation).

Under this `eval` folder, there are three scripts:

1. `qns_generation.py`: Generates questions from Azure Search Index
2. `ans_generation.py`: Generates answers for apre-defined question bank
3. `eval.py`: Evaluates the generated answers, questions and retrieved chunks using the Deepeval framework.

## Installation Guide

You can activate the environment that has been setup for this repo and install the dependencies using the following commands:

For UNIX-based systems (macOS / Linux):

```shell
# Activate virtual environment
source .venv\bin/activate

# change to eval directory
cd eval

# Install dependencies
pip install -r requirements.txt
```

For Windows:

```shell
# Activate virtual environment
source .venv\Scripts\activate

# change to eval directory
cd eval

# Install dependencies
pip install -r requirements.txt
```

Login to your Azure account:

```shell
azd auth login
```

## Question Generation

### Inputs file(s) for question generation

Save the following files in the `input` subfolder.

1. `merged_data.parquet`: output file from the content-optimisation kedro data-processing pipeline
2. `final_kws_for_qns_generation.xlsx`: excel file containing the following columns:
    - `method`: method for question generation (by_content_category / by_pg_views)
    - `content_category`: content category
    - `subpage`: subpage of the content_category (applicable only for programs articles)
    - `final_keywords`: topic keywords generated via BERTopic

### Running the script for `qns_generation.py`

```shell
python qns_generation.py --readfilepath input/final_kws_for_qns_generation.xlsx --usevectorsearch --usetextsearch --usesemanticranker
```

The following table details the command-line argument(s) available:
| Argument              | Description                                      | Default Value                                |
|---------------------------------------------|---------------------------------------|---------------------------------------------|
| `--readfilepath`       | File path to read input file                 | `./input/final_kws_for_qns_generation.xlsx`          |
| `--searchmaxresults`   | Number of search results for generation by content category                            | `30`                                        |
| `--searchmaxresultspgviews`   | Number of search results for generation by top page views                            | `10`                                        |
| `--temperatureqns`   | Temperature for question generation                            | `0.3`                                        |
| `--temperatureans`   | Temperature for answer generation                            | `0.3`                                        |
| `--usevectorsearch`    | Enables vector-based search functionality        | `False` if not specified                    |
| `--usetextsearch`      | Enables text-based search functionality          | `False` if not specified                    |
| `--usesemanticranker`  | Enables semantic ranking mechanism               | `False` if not specified                    |
| `--usesemanticcaptions`| Enables semantic captions                        | `False` if not specified                    |
| `--minsearchscore`     | Threshold for minimum search score               | `0.0`                                       |
| `--minrerankerscore`   | Threshold for minimum re-ranker score            | `0.0`                                       |
| `--responsetokenlimit`   | Response token limit            | `512`                                       |
| `--seed`   | Seed for reproducibility            | `1234`                                       |

### Question generation output

A successful `qns_generation.py` script run will save the generated questions and source information in a CSV file under the `output` folder, named `question_bank_<date>_<time>.xlsx`.

## Answer Generation

The `ans_generation.py` generates answers for a pre-defined question bank.

### Inputs file(s) for answer generation

You are required to upload a csv file with questions under the `input` subfolder. Ensure that that the column header is `question`.

<img src="../docs/images/deepeval_input_csv_sample.png" alt="CSV file input" width="350">

### Running the script for `ans_generation.py`

Run the following command:

```shell
python ans_generation.py --readfilepath input/sample_question_bank.csv --usevectorsearch --usetextsearch --usesemanticranker
```

The following table details the command-line argument(s) available:

| Argument              | Description                                      | Default Value                                |
|---------------------------------------------|---------------------------------------|---------------------------------------------|
| `--readfilepath`       | File path to read input file                 | `./input/sample_question_bank.csv`          |
| `--selectedlanguage`   | Selected language. Only `en`, `zh`, `ms`, `ta` are allowed                            | `en`                                        |
| `--usevectorsearch`    | Enables vector-based search functionality        | `False` if not specified                    |
| `--usetextsearch`      | Enables text-based search functionality          | `False` if not specified                    |
| `--usesemanticranker`  | Enables semantic ranking mechanism               | `False` if not specified                    |
| `--usesemanticcaptions`| Enables semantic captions                        | `False` if not specified                    |
| `--topn`               | Top N documents to retrieve                  | `3`                                         |
| `--weight`             | Weightage on vector search against text search   | `1.0`                                       |
| `--querylanguage`      | Query language                               | `en-us`                                     |
| `--queryspeller`       | Query speller                                | `lexicon`                                   |
| `--minsearchscore`     | Threshold for minimum search score               | `0.0`                                       |
| `--minrerankerscore`   | Threshold for minimum re-ranker score            | `0.0`                                       |
| `--queryresponsetokenlimit`   | Query response token limit            | `100`                                       |
| `--responsetokenlimit`   | Response token limit            | `512`                                       |
| `--savefilepath`   | File path where evaluation results will be saved            | `./output/generated_answers_for_eval.csv`                                       |
| `--debug`   | Enable debug logging            | `False` if not specified`                                       |
| `--seed`   | Seed for reproducibility            | `1234`                                       |

### Answer generation output

A successful `ans_generation.py` script run will save the generated answers and source information in a CSV file under the `output` folder, named `generated_answers_for_eval.csv`.

## Deepeval Evaluation

 `eval.py` evaluates the generated question using the Deepeval framework. The metrics used from Deepeval are Answer Relevancy, Faithfulness and Contextual Relevancy.

### Inputs file(s) for evaluation

This script uses the output (`generated_answers_for_eval.csv`) from `ans_generation.py` for evaluation. No further input files required.

### Running the `eval.py` script

Run the following command:

```shell
python eval.py --readfilepath output/generated_answers_for_eval.csv --model gpt-4o-mini --asyncmode
```

The following table details the command-line argument(s) available:
| Argument        | Description                                      | Default Value                                |
|------------------|--------------------------------------------------|----------------------------------------------|
| `--readfilepath`  | The file path to read input file                | `./output/generated_answers_for_eval_test.csv` |
| `--model`        | Azure OpenAI GPT model for evaluation. Accepted values: `gpt-4o` / `gpt-4o-mini            | `gpt-4o`                                    |
| `--asyncmode`    | Enables asynchronous programming                 | `False` if not specified                    |

#### Using gpt-4o-mini

If using gpt-4o-mini for evaluation, create a `.env` file in the `eval` folder with these credentials:

```shell
# Azure OpenAI Services
AZURE_OPENAI_API_TYPE="..."
AZURE_OPENAI_API_VERSION="..."
AZURE_OPENAI_CHATGPT_DEPLOYMENT="..." # Deployment name
AZURE_OPENAI_SERVICE="..." # Resource name
```

Set the `AZURE_OPENAI_API_VERSION` to the latest version mentioned [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation).

#### Async vs Sync mode

The pros and cons of running in async mode vs in sync mode are detailed in the table below:

|                | async mode                                 | sync mode                                               |
|----------------|---------------------------------------------|---------------------------------------------------------|
| **Pros**       | Faster                                      | Able to generate full results even if there are test cases with error |
| **Cons**       | If there is error for any one of the test case (e.g., content filter, rate limit), interim results will not be saved. | Slower                                                  |

Even though async mode runs faster than sync mode, sync mode is preferred in order to conveniently debug any errors encountered during evaluation.

### Evaluation output

A successful `eval.py` script run will save the evaluation results under the `output` folder in a file named `deepeval_results_<model_name>_<date>_<time>.csv`.
