import json
import yaml

with open("test_files/vpc_cf_example.json") as cf_json:
    cf_data = json.load(cf_json)

trust_boundaries = []

for i in cf_data['Resources']:
    # if the resource is a VPC
    if cf_data['Resources'][i]['Type'] == 'AWS::EC2::VPC':
        nested_boundaries = []
        # look through the other resources for subnets and keep track in a list any that are subnets in this VPC
        for j in cf_data['Resources']:
            if cf_data['Resources'][j]['Type'] == 'AWS::EC2::Subnet':
                if cf_data['Resources'][j]['Properties']['VpcId']['Ref'] == i:
                    nested_boundaries.append(j.lower())
        # the nested trust boundaries that we just found will be included in the append
        trust_boundaries.append({i: {'id': i.lower(), 'type':'network-cloud-security-group', 'tags':'', 'technical_assets_inside':'', 'trust_boundaries_nested': [nested_boundaries]}})

    elif cf_data['Resources'][i]['Type'] == 'AWS::EC2::Subnet':
        # if the resource is a subnet, then just add it as a trust boundary with no nested boundaries
        trust_boundaries.append({i: {'id': i.lower(), 'type':'network-cloud-security-group', 'tags':'', 'technical_assets_inside':'', 'trust_boundaries_nested':''}})

# print(trust_boundaries)

for i in trust_boundaries:
    # this is the output that will go in the trust_boundaries section of the threagile input
    # right now it will still need to be manually massaged just a tad, but we can fix that later
    # within the trust boundaries section we also need to add mapping to technical assets, once we figure out how to approach those
    print(yaml.dump(i))