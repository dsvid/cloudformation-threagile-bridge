# cloudformation-threagile-bridge
a project to automatically translate (some) AWS CloudFormation constructs to Threagile's asset/communication link/trust boundary model to aid with agile threat modelling using Threagile (https://threagile.io/)

## What does it do?

This script takes an existing threagile yaml input file, and a Cloud Formation template (either yaml or json).

It will trawl through the Cloud Formation template and look for certain resources, etc. and map them to threagile threat modelling concepts.

This is based on a set of heuristics defined in the code itself. Essentially a set of rules (similar to Threagile's rules).

It will then output an updated threagile yaml file which includes the existing threagile yaml definitions, as well as any additional trust boundaries, assets, communication links, etc. which it has found.

## What is it/what is it not?

This tool is designed to help make the process of threat modelling using Threagile (https://threagile.io/) easier and more automated.

It is not designed to *fully* automate a threat modelling workflow, as there will be translations which are not captured by this tool. 

We are hoping that it will help to ease *some* of the manual work of defining assets/communication links/etc. in threagile's yaml inputs.

Over time, we aim to add more translation rules with the goal of automating threat modelling as many CloudFormation resource types as possible, but this will be an ongoing process as this tool matures.

## How to run?

First make sure the requirements are installed (currently only pyyaml)

```
pip install -r requirements.txt
```

Currently the script requires 3 arguments:
- path to CF template (either yaml or json)
- path to existing threagile yaml to be added to. This might already have some content populated manually.
- path to output updated threagile yaml to

For example, you might run it like:

```
python main.py "test_files/vpc_cf_example.json" "test_files/threagile-stub-input.yaml" "test_files/output_yaml.yaml"
```

The output file can then be run through Threagile by following its readme https://github.com/Threagile/threagile 

If you have Docker installed and have output to a file called "output_yaml.yaml" an example threagile run command might look like:

```
docker run --rm -it -v "$(pwd)":/app/work threagile/threagile -verbose -model /app/work/output_yaml.yaml -output /app/work
```
## What would a workflow using this tool + Threagile look like?

We expect that a developer would start with a stub threagile model and fill in the non-automatable parts, e.g. descriptions, business and technical overview, author, etc. as well as any architectural elements which are not yet captured in the cloudformation-threagile-bridge rules.

Then this tool can be run to automatically capture concepts defined in a Cloud Formation template (can also be used with CDK by compiling the CDK template into Cloud Formation).

This could be done either on the local command line before a commit, or in a pipeline.

## Can I add new rules/heuristics

Yes! AWS has a lot of tools available, and we will likely not be able to capture them all in this tool even as the tool matures (AWS keep adding more stuff!). 

We have also made this tool open source, with the intention of allowing you to define your own additional rules for CloudFormation to Threagile translation depending on your use case. This is similar to the way that Threagile provides the ability to define custom rules.

## What does it not yet do?

This project is still in progress, so the number of Cloud Formation -> Threagile mappings is currently limited. We are continuing to add more mappings, and this will be an ongoing process.

Beyond more mappings, the primary features that I am hoping to add is a report of which Cloud Formation concepts have been auto-mapped, and which have not, plus the ability to detect when a CloudFormation concept has already been mapped (so as not to duplicate it).

Additionally, my current to-do list is:

- split up the project into separate files
- add translation of communication links
- expand the list of existing translations
- make the existing translations "smarter" (there are still some hardcoded values, e.g. technical asset 'technology' is hardcoded to 'web-service-rest' to just get things up and running)
- add unit tests

## Are you associated with Threagile?

No, we are not. We just like Threagile, and want to make using it as automated as possible.
