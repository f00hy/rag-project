# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/f00hy/rag-project/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                           |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| app/\_\_init\_\_.py            |        0 |        0 |        0 |        0 |    100% |           |
| app/api/\_\_init\_\_.py        |        0 |        0 |        0 |        0 |    100% |           |
| app/api/main.py                |        5 |        0 |        0 |        0 |    100% |           |
| app/api/routes/\_\_init\_\_.py |        0 |        0 |        0 |        0 |    100% |           |
| app/api/routes/crawl.py        |       28 |        0 |        6 |        0 |    100% |           |
| app/api/routes/query.py        |       23 |        0 |        0 |        0 |    100% |           |
| app/api/schemas.py             |       19 |        0 |        0 |        0 |    100% |           |
| app/config.py                  |       16 |        0 |        0 |        0 |    100% |           |
| app/infra/\_\_init\_\_.py      |        0 |        0 |        0 |        0 |    100% |           |
| app/infra/cfr2.py              |       11 |        2 |        0 |        0 |     82% |     22-23 |
| app/infra/postgres.py          |       14 |        4 |        0 |        0 |     71% |     28-31 |
| app/infra/qdrant.py            |       14 |        7 |        2 |        0 |     44% |     22-64 |
| app/logging\_config.py         |        4 |        0 |        0 |        0 |    100% |           |
| app/main.py                    |       30 |       10 |        0 |        0 |     67% |     34-44 |
| app/models.py                  |       22 |        0 |        0 |        0 |    100% |           |
| app/pipelines/\_\_init\_\_.py  |        0 |        0 |        0 |        0 |    100% |           |
| app/pipelines/generation.py    |       64 |        7 |        8 |        0 |     88% |   120-127 |
| app/pipelines/ingestion.py     |       42 |        0 |        6 |        0 |    100% |           |
| app/pipelines/retrieval.py     |       24 |        0 |        4 |        0 |    100% |           |
| app/services/\_\_init\_\_.py   |        0 |        0 |        0 |        0 |    100% |           |
| app/services/chunking.py       |       38 |        0 |        4 |        0 |    100% |           |
| app/services/crawling.py       |       28 |        0 |        4 |        0 |    100% |           |
| app/services/embedding.py      |       28 |        0 |        0 |        0 |    100% |           |
| app/services/indexing.py       |       39 |        1 |        4 |        0 |     98% |        25 |
| app/services/reranking.py      |       17 |        0 |        0 |        0 |    100% |           |
| app/services/searching.py      |       15 |        0 |        2 |        0 |    100% |           |
| **TOTAL**                      |  **481** |   **31** |   **40** |    **0** | **93%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/f00hy/rag-project/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/f00hy/rag-project/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/f00hy/rag-project/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/f00hy/rag-project/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Ff00hy%2Frag-project%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/f00hy/rag-project/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.