# sampleplan

This software project accompanies the research paper, [On Efficient and Statistical Quality Estimation for Data Annotation](https://arxiv.org/abs/2405.11919). Find a demo of the tool at: https://www.acceptancesampling.com/.

`sampleplan` is a tool to determine sample sizes required for data quality control. It supports sample size calculation for:

- Clopper-Pearson exact confidence intervals with and without mid-P
- Single Acceptance Sampling
- Double Acceptance Sampling
- Sequential Acceptance Sampling

for the binomial (sampling with replacement) and hypergeometric (sampling without replacement) distributions. 

> This repository contains experimental software and is published for the sole purpose of giving additional background details on the respective publication.

## Citation

```
@inproceedings{klie2024onEfficient,
	title        = {On Efficient and Statistical Quality Estimation for Data Annotation},
	author       = {Jan-Christoph Klie and Juan Haladjian and Marc Kirchner and Rahul Nair},
	year         = 2024,
	booktitle    = {The 62nd Annual Meeting of the Association for Computational Linguistics}
}
```

## Installation

This software is not yet published to PyPi. To install, run

```bash
pip install git+https://github.com/apple/ml-sampleplan
```

## Command line usage

Installing the package also installs the `sampleplan` command. It exposes the full functionality of the
library; the main parser selects the method, each method has its own arguments:

```bash
sampleplan --help
sampleplan single --help
```

The distribution is selected with `-d/--distribution` (`binomial` or `hypergeometric`), where
`--lot-size` is required for the hypergeometric case. Every command accepts `--json` to print a
machine-readable result instead of plain text.

### Confidence intervals

```bash
sampleplan ci -d binomial --p0 0.01 --alpha 0.05 --ci-half-width 0.01
sampleplan ci -d hypergeometric --lot-size 1000 --p0 0.01 --alpha 0.05 --ci-half-width 0.01
```

Use `--method` to switch between the Clopper-Pearson `exact` interval (default), the `mid-p`
corrected one and the `agresti-coull` approximation (binomial only).

### Single sampling

```bash
sampleplan single -d binomial --p-a 0.01 --p-r 0.05 --alpha 0.05 --beta 0.2
sampleplan single -d hypergeometric --p-a 0.01 --p-r 0.05 --alpha 0.05 --beta 0.2 --lot-size 1000
```

### Double sampling

```bash
sampleplan double -d binomial --p-a 0.01 --p-r 0.05 --alpha 0.05 --beta 0.2
sampleplan double -d hypergeometric --p-a 0.01 --p-r 0.05 --alpha 0.05 --beta 0.2 --lot-size 1000
```

Besides the plan itself, this prints the average sample size for the full and the curtailed variant.
Pass `--p` to evaluate them at an error rate other than `--p-a`.

### Sequential sampling

```bash
sampleplan sequential -d binomial --p-a 0.01 --p-r 0.05 --alpha 0.05 --beta 0.2 --p 0.07
sampleplan sequential -d hypergeometric --p-a 0.01 --p-r 0.05 --alpha 0.05 --beta 0.2 \
    --lot-size 1000 --defects 4 --print-limits
```

The plan is truncated at `--cutoff`, which defaults to three times the single sampling plan sample
size for the binomial case and to the single sampling plan sample size for the hypergeometric one.
`--print-limits` additionally prints the acceptance and rejection limits for every step.

## Web UI and API

Install the optional web dependencies and start the server:

```bash
pip install ".[web]"
sampleplan-web
```

The calculator is available at [http://localhost:8000](http://localhost:8000), and the interactive
Swagger documentation is at [http://localhost:8000/docs](http://localhost:8000/docs). The host and
port can be changed with `SAMPLEPLAN_HOST` and `SAMPLEPLAN_PORT`.

To keep public API requests bounded, lot size, binomial search limit, double-sampling ratio and
sequential cutoff have safe defaults. Operators can tune them with `SAMPLEPLAN_MAX_LOT_SIZE`,
`SAMPLEPLAN_MAX_SEARCH_LIMIT`, `SAMPLEPLAN_MAX_DOUBLE_RATIO` and `SAMPLEPLAN_MAX_SEQUENTIAL_CUTOFF`
respectively.

Each CLI calculation has a matching JSON endpoint:

| CLI command | REST endpoint |
| --- | --- |
| `sampleplan ci` | `POST /api/ci` |
| `sampleplan single` | `POST /api/single` |
| `sampleplan double` | `POST /api/double` |
| `sampleplan sequential` | `POST /api/sequential` |

For example:

```bash
curl http://localhost:8000/api/single \
  -H 'content-type: application/json' \
  -d '{"distribution":"binomial","p_a":0.01,"p_r":0.05}'
```

To build and run the container locally:

```bash
docker build -t sampleplan .
docker run --rm -p 8000:8000 sampleplan
# Or:
docker compose up
```

Published images from `main` can be run directly from GitHub Container Registry:

```bash
docker run --rm -p 8000:8000 ghcr.io/psytechlab/ml-sampleplan:latest
```

## Usage

The following section describes how to use this package to compute sample sizes for confidence intervals
and acceptance sampling that give certain statistical guarantees. We implement all for the binomial (sampling with replacement)
and hypergeometric (sampling without replacement) distributions.

The following parameters describe the statistical guarantees one wants from the tests:

- **alpha**: Rejecting a lot that should have been accepted (producer's risk)
- **beta**: Accepting a lot that should have been rejected (consumer's risk)
- **p0/p**: The assumed error rate, the closer it is to .5, the larger the sample size required typically is for binomial and hypergeometric distributions 
- **half_width**: The size of the confidence interval in one direction
- **p_a**: Acceptable ratio of defective items in a lot
- **p_r**: Unacceptable ratio of defective items in a lot

### Confidence Intervals

#### Binomial

```python
from sampleplan.confidence_interval import sample_size_exact_binomial

p0 = 0.01
alpha = 0.05
ci_half_width = 0.01

n_binomial = sample_size_exact_binomial(p0, alpha, ci_half_width)
```

#### Hypergeometric

```python
from sampleplan.confidence_interval import sample_size_exact_hypergeometric

lot_size = 1000
p0 = 0.01
alpha = 0.05
ci_half_width = 0.01

n_binomial = sample_size_exact_hypergeometric(lot_size, p0, alpha, ci_half_width)
```

### Single Sampling

A single sample of size *n* is inspected. If it contains more annotation errors than the critical value *c*, it is 
rejected, otherwise, it is accepted.

#### Binomial

```python
from sampleplan.acceptance_sampling import SingleSamplingPlan

alpha = 0.05
beta = 0.2
p_a = 0.01
p_r = 0.05

plan = SingleSamplingPlan.binomial(p_a, p_r, alpha, beta)
print(f"Single Sampling Plan binomial: n={plan.n}, c={plan.c}")
```

#### Hypergeometric

```python
from sampleplan.acceptance_sampling import SingleSamplingPlan

alpha = 0.05
beta = 0.2
p_a = 0.01
p_r = 0.05
lot_size = 1000

plan = SingleSamplingPlan.hypergeometric(p_a, p_r, alpha, beta, lot_size)
print(f"Single Sampling Plan hypergeometric: n={plan.n}, c={plan.c}")
```

### Double Sampling

Instead of taking a single sample, in double sampling, batches are accepted or rejected based on two (usually smaller) samples.
At first, a sample of size *n_1* is taken and inspected.
If it contains less defects than a lower limit *c_1*, it is accepted, if it contains more defects than an upper limit *c_2*, it is rejected.
If the number of defects it is between both, then a second sample is taken; the batch is rejected if the number of defects in both samples combined is larger than *c_2*. 
The advantage is that in the happy case, only *n_1* samples need to be inspected, thereby saving time and money. 
In order to make the actual computation more tractable, we only use double-stage plans such that *n_1 = n_2* . 
We implement two versions of double sampling, **full* where samples are always completely inspected and **curtailed*, where inspection of the second sample is stopped in case there are more than *c_2* defects found.
It is recommended to always at least look at the first *n_1* samples in order to get an estimate for the error rate, we will follow this textbook advice in this paper.


#### Binomial

```python
from sampleplan.acceptance_sampling import DoubleSamplingPlan

alpha = 0.05
beta = 0.2
p_a = 0.01
p_r = 0.05

plan = DoubleSamplingPlan.binomial(p_a, p_r, alpha, beta)
print(f"Doube Sampling Plan binomial: n1=n2=n={plan.n}, c1={plan.c1}, c2={plan.c2}")
```

#### Hypergeometric

```python
from sampleplan.acceptance_sampling import DoubleSamplingPlan

alpha = 0.05
beta = 0.2
p_a = 0.01
p_r = 0.05
lot_size = 1000

plan = DoubleSamplingPlan.hypergeometric(p_a, p_r, alpha, beta, lot_size)
print(f"Doube Sampling Plan binomial: n1=n2=n={plan.n}, c1={plan.c1}, c2={plan.c2}")
```

### Sequential Sampling

A generalization of double sampling is sequential sampling.
It is based on the sequential probability ratio test by Wald.
In this setting, instances in a batch are inspected one by one and after each step, it is decided whether to continue or stop and accept or reject.
The acceptance and rejection boundaries  are computed at every step from *p_a* and *p_r*, *\alpha* and *\beta* as well as the number of incorrect and total instances inspected so far.
It can happen that the whole batch needs to be inspected, especially if the actual error rate is between *p_a* and *p_r*.
As this is an undesirable outcome, we truncate at the sample size of single sampling and accept or reject based on its critical value.
Note that This is an approximation, computing an optimal curtailment in general is quite difficult.

#### Binomial

```python
from sampleplan.acceptance_sampling import BinomialSequentialSamplingPlan, SingleSamplingPlan

alpha = 0.05
beta = 0.2
p_a = 0.01
p_r = 0.05

p = 0.07

plan = BinomialSequentialSamplingPlan(p_a, p_r, alpha, beta)
asn = plan.average_sample_number(p)

# For curtailing, we stop if we did not make a decision when reaching 3x the Single Sampling Plan sample size
# This is recommended by Montgomery, D. (2005), Introduction to Statistical Quality Control 
# as binomial sequential sampling has no natural stopping point due to sampling with replacement.
ssp = SingleSamplingPlan.binomial(p_a, p_r, alpha, beta)
asn_curtailed = plan.average_sample_with_cutoff(p, ssp.n * 3)
```

#### Hypergeometric

```python
from sampleplan.acceptance_sampling import HypergeometricSequentialSamplingPlan, SingleSamplingPlan

alpha = 0.05
beta = 0.2
p_a = 0.01
p_r = 0.05
lot_size = 1000
defects_in_lot = 4  # For simulation purposes, this is just known post inspection the whole lot

plan = HypergeometricSequentialSamplingPlan(p_a, p_r, alpha, beta, lot_size)
borders = plan.compute_truncated_wald_region()
asn = plan.average_sample_number(defects_in_lot)

# For curtailing, we stop if we did not make a decision when reaching the Single Sampling Plan sample size 
ssp = SingleSamplingPlan.hypergeometric(p_a, p_r, alpha, beta, lot_size)
borders_curtailed = plan.compute_truncated_wald_region(cutoff=ssp.n)

for i in range(borders_curtailed.num_trials):
    print(f"Items inspected: \t{i}\tAccept if num_errors < {borders_curtailed.lower_limits[i]}\tReject if num errors > {borders_curtailed.upper_limits[i]}")
```

## Development

This project uses `poetry` to manage the build process as well as dependencies.

You can format the code via

    make format

which should be run before every commit.

You can run the tests via

    make test
