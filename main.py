import json
import yaml
import os

path_to_json = os.path.join("test_files", "vpc_cf_example.json")

with open(path_to_json) as cf_json:
    cf_data = json.load(cf_json)

# initialize the different categories we want to capture for threagile's input
trust_boundaries = {}
technical_assets = {}
data_assets = {}
communication_links = {}

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
                    if cf_data['Resources'][j]['Properties']['VpcId']['Ref'] == i:
                        nested_boundaries.append(j.lower())
            # the nested trust boundaries that we just found will be included in the append
            trust_boundaries[i] = {
                    'id': i.lower(), 
                    'type':'network-cloud-security-group', 
                    # 'tags':'', 
                    # 'technical_assets_inside':'', 
                    'trust_boundaries_nested': nested_boundaries
                }

        elif cf_data['Resources'][i]['Type'] in inner_trust_boundaries_types:
            # if the resource is a subnet, then just add it as a trust boundary with no nested boundaries
            trust_boundaries[i] = {
                    'id': i.lower(), 
                    'type':'network-cloud-security-group', 
                    # 'tags':'', 
                    # 'technical_assets_inside':'', 
                    # 'trust_boundaries_nested':''
                }

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
            for j in cf_data['Resources'][i]['Properties']:
                # check for references to trust boundaries and add them as links if found
                if 'Ref' in cf_data['Resources'][i]['Properties'][j]:
                    # just used lower() here because we use the lowercase earlier for the id...
                    # probably better to reference the actual id of the trust boundary that we defined earlier
                    # but I just want to get this working lol...
                    dict_temp = {'technical_assets_inside': [i.lower()]}
                    if cf_data['Resources'][i]['Properties'][j]['Ref'] in trust_boundaries:
                        trust_boundaries[cf_data['Resources'][i]['Properties'][j]['Ref']].update(dict_temp)
                    # print(i)
                    # print(cf_data['Resources'][i]['Properties'][j]['Ref'])
                    # print(cf_data['Resources'][i]['Properties'][j])



parse_cf_resources_for_trust_boundaries(cf_data)
parse_cf_resources_for_technical_assets(cf_data)

print(yaml.dump(trust_boundaries, default_flow_style=False))

print("\n")

print(yaml.dump(technical_assets, default_flow_style=False))
