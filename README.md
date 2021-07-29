# The Book of Ambramelin
<sup>Not to be confused with [The Book of Abramelin](https://en.wikipedia.org/wiki/The_Book_of_Abramelin).</sup>

A CLI for commonly-used Ambra API operations.

This can be thought of as an opinionated CLI wrapper around the [Ambra SDK](https://github.com/dicomgrid/sdk-python).

## Quickstart

### Installation

1. Clone this repository
2. Install dependencies: `poetry install`

TODO:
* homebrew formula
* [executable](https://packaging.python.org/overview/#bringing-your-own-python-executable)

### Usage

Before you can use the `ambra` command, you must `poetry shell`.

Add a user:

```
abmra user add user@domain.com
```

> You will be prompted for a password which will be stored in your keychain.

Configure an environment:

```
ambra env add staging https://test.ambrahealth.com/api/v3 --user user@domain.com
ambra env use staging
```

Fetch a study:

```
ambra study get a93208f1-84d6-47bd-90c5-0d303e561282 --fields engine_fqdn storage_namespace study_uid

{
  "storage_namespace": "3efbb421-282c-419c-a862-c1aabd456de9",
  "engine_fqdn": "storelup04.dicomgrid.com",
  "study_uid": "1.2.826.0.1.3680043.6.38621.89741.20171011130712.1280.9.14"
}
```

or a bunch of them:

```
ambra study list uuid.in.a93208f1-84d6-47bd-90c5-0d303e561282,b7f8f519-3f6e-4824-83c6-dff9b10f832c \
  --fields study_uid

[
  {
    "study_uid": "1.2.826.0.1.3680043.8.498.82739480818172868271983745911501828890"
  },
  {
    "study_uid": "1.2.826.0.1.3680043.6.38621.89741.20171011130712.1280.9.14"
  }
]
```