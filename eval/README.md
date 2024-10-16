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

To be updated

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
| `--readfilepath`       | The file path to read input file                 | `./input/sample_question_bank.csv`          |
| `--selectedlanguage`   | The selected language. Only `en`, `zh`, `ms`, `ta` are allowed                            | `en`                                        |
| `--usevectorsearch`    | Enables vector-based search functionality        | `False` if not specified                    |
| `--usetextsearch`      | Enables text-based search functionality          | `False` if not specified                    |
| `--usesemanticranker`  | Enables semantic ranking mechanism               | `False` if not specified                    |
| `--usesemanticcaptions`| Enables semantic captions                        | `False` if not specified                    |
| `--topn`               | The top N documents to retrieve                  | `3`                                         |
| `--weight`             | Weightage on vector search against text search   | `1.0`                                       |
| `--querylanguage`      | The query language                               | `en-us`                                     |
| `--queryspeller`       | The query speller                                | `lexicon`                                   |
| `--minsearchscore`     | Threshold for minimum search score               | `0.0`                                       |
| `--minrerankerscore`   | Threshold for minimum re-ranker score            | `0.0`                                       |

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

```.env
# Azure OpenAI Services
AZURE_OPENAI_API_TYPE="..."
AZURE_OPENAI_API_VERSION="..."
AZURE_OPENAI_CHATGPT_DEPLOYMENT="..."
AZURE_OPENAI_SERVICE="..."
```

#### Async vs Sync mode

The pros and cons of running in async mode vs in sync mode are detailed in the table below:

|                | async mode                                 | sync mode                                               |
|----------------|---------------------------------------------|---------------------------------------------------------|
| **Pros**       | Faster                                      | Able to generate full results even if there are test cases with error |
| **Cons**       | If there is error for any one of the test case (e.g., content filter, rate limit), interim results will not be saved. | Slower                                                  |

Even though async mode runs faster than sync mode, sync mode is preferred in order to conveniently debug any errors encountered during evaluation.

### Evaluation output

A successful `eval.py` script run will save the evaluation results under the `output` folder in a file named `deepeval_results_<model_name>_<date>_<time>.csv`.
