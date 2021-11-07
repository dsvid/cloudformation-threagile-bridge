import json
import yaml
import sys
import os

path_to_cf_template = sys.argv[1]
path_to_threagile_input_yaml = sys.argv[2]
path_to_threagile_output_yaml = sys.argv[3]

cf_file_extension = os.path.splitext(path_to_cf_template)[-1]

assert(cf_file_extension in [".yaml", ".json"]), "input must be json or yaml"

if cf_file_extension == ".json":
    # open the cf template
    with open(path_to_cf_template) as cf_json:
        cf_data = json.load(cf_json)
elif cf_file_extension == ".yaml":
    with open(path_to_cf_template) as cf_yaml:
        cf_data = yaml.safe_load(cf_yaml)

# open the starting threagile yaml
with open(path_to_threagile_input_yaml) as existing_thrg:
    thrg_yaml_parsed = yaml.safe_load(existing_thrg)

resources_not_mapped = []
resources_mapped = []

for i in cf_data['Resources']:
    resources_not_mapped.append(i)

# print(yaml.dump(thrg_yaml_parsed, default_flow_style=False))

# initialize the different categories we want to capture for threagile's input
trust_boundaries = {}
technical_assets = {}
data_assets = {}
communication_links = {}

# initialize the yaml output (could just overwrite the existing thrg_yaml_parsed)
yaml_output = thrg_yaml_parsed

# the AWS resource types that we want to auto-parse into certain categories
outer_trust_boundaries_types = [
    'AWS::EC2::VPC'
]

inner_trust_boundaries_types = [
    'AWS::EC2::Subnet',
    'AWS::EC2::RouteTable'
]

technical_asset_types = [
    'AWS::EC2::Route',
    'AWS::EC2::NatGateway',
    'AWS::EC2::EIP',
    'AWS::EC2::InternetGateway'
]

def mark_resource_as_mapped(resource):
    resources_not_mapped.remove(resource)
    resources_mapped.append(resource)

def parse_cf_resources_for_trust_boundaries(cf_template):
    '''
    parses 'Resources' from cf data
    '''
    for i in cf_data['Resources']:
        # if the resource is a VPC
        if cf_data['Resources'][i]['Type'] in outer_trust_boundaries_types:
            nested_boundaries = []
            # look through the other resources for subnets and keep track in a list any that are subnets in this VPC
            for j in cf_data['Resources']:
                if cf_data['Resources'][j]['Type'] in inner_trust_boundaries_types:
                    try:
                        if cf_data['Resources'][j]['Properties']['VpcId']['Ref'] == i:
                            nested_boundaries.append(j.lower())
                    except KeyError:
                        print(j, "has no properties")
            # the nested trust boundaries that we just found will be included in the append
            trust_boundaries[i] = {
                    'id': i.lower(), 
                    'type':'network-cloud-security-group', 
                    # 'tags':'', 
                    # 'technical_assets_inside':'', 
                    'trust_boundaries_nested': nested_boundaries
                }
            mark_resource_as_mapped(i)

        elif cf_data['Resources'][i]['Type'] in inner_trust_boundaries_types:
            # if the resource is a subnet, then just add it as a trust boundary with no nested boundaries
            trust_boundaries[i] = {
                    'id': i.lower(), 
                    'type':'network-cloud-security-group', 
                    # 'tags':'', 
                    # 'technical_assets_inside':'', 
                    # 'trust_boundaries_nested':''
                }
            mark_resource_as_mapped(i)

def parse_cf_resources_for_technical_assets(cf_template):
    # means we're trawling the template a few times, but just a bit easier for now cos we want to
    # add references to trust boundaries, and it's easier if we've already found them all
    for i in cf_data['Resources']:
        if cf_data['Resources'][i]['Type'] in technical_asset_types:
            technical_assets[i] = {
                'id': i.lower(), 
                'type': 'process', # values: external-entity, process, datastore
                'usage': 'business', # values: business, devops
                'size': 'component', # values: system, service, application, component
                'technology': 'web-service-rest', # values: see help
                'machine': 'virtual', # values: physical, virtual, container, serverless
                'encryption': 'none', # values: none, transparent, data-with-symmetric-shared-key, data-with-asymmetric-shared-key, data-with-enduser-individual-key
                'confidentiality': 'confidential', # values: public, internal, restricted, confidential, strictly-confidential
                'integrity': 'critical', # values: archive, operational, important, critical, mission-critical
                'availability': 'critical', # values: archive, operational, important, critical, mission-critical
            }
            mark_resource_as_mapped(i)
            try:
                for j in cf_data['Resources'][i]['Properties']:
                    # check for references to trust boundaries and add them as links if found
                    if 'Ref' in cf_data['Resources'][i]['Properties'][j]:
                        # just used lower() here because we use the lowercase earlier for the id...
                        # probably better to reference the actual id of the trust boundary that we defined earlier
                        # but I just want to get this working lol...
                        dict_temp = {'technical_assets_inside': [i.lower()]}
                        if cf_data['Resources'][i]['Properties'][j]['Ref'] in trust_boundaries:
                            trust_boundaries[cf_data['Resources'][i]['Properties'][j]['Ref']].update(dict_temp)
            except KeyError:
                print(i, "has no properties")


print("parsing CF template for trust boundaries")
parse_cf_resources_for_trust_boundaries(cf_data)

print("parsing CF template for trust technical assets")
parse_cf_resources_for_technical_assets(cf_data)


# if the existing yaml was empty for the parts we're going to add to, then initialize them
if yaml_output['technical_assets'] is None:
    yaml_output['technical_assets'] = {}

if yaml_output['trust_boundaries'] is None:
    yaml_output['trust_boundaries'] = {}


# add the things that we've translated to the existing parsed yaml
print("adding parsed trust boundaries to parsed threagile yaml input")
yaml_output['trust_boundaries'].update(trust_boundaries)

print("adding parsed technical assets to parsed threagile yaml input")
yaml_output['technical_assets'].update(technical_assets)


with open(path_to_threagile_output_yaml, 'w') as output:
    # will print with the same ordering of root elements
    # not needed per yaml spec, but nicer for readability
    print("writing updated threagile yaml to output file")
    for i in yaml_output:
        print(yaml.dump({i: yaml_output[i]}, default_flow_style=False), file=output)

# for i in trust_boundaries:
#     print(i)
# for i in technical_assets:
#     print(i)
# for i in data_assets:
#     print(i)
# for i in communication_links:
#     print(i)
# print("\n")

print("resources mapped", resources_mapped)
print("resources not mapped", resources_not_mapped)

print("done")