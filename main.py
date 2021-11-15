import json, yaml, sys, os

# parse the command line arguments
path_to_cf_template = sys.argv[1]
path_to_threagile_input_yaml = sys.argv[2]
path_to_threagile_output_yaml = sys.argv[3]

# store the file extension of the CF template and validate that it's either yaml or json
cf_file_extension = os.path.splitext(path_to_cf_template)[-1]
assert(cf_file_extension in [".yaml", ".json"]), "input must be json or yaml"

# map the path to the resource rules file to the correct OS path syntax
resource_rules_path = os.path.join("rules", "resource_rules.yaml")

# open and parse the resource rules
with open(resource_rules_path) as resource_rules_file:
    resource_rules = yaml.safe_load(resource_rules_file)

# open and parse the input CF template
if cf_file_extension == ".json":
    # open the cf template
    with open(path_to_cf_template) as cf_json:
        cf_data = json.load(cf_json)
elif cf_file_extension == ".yaml":
    with open(path_to_cf_template) as cf_yaml:
        cf_data = yaml.safe_load(cf_yaml)

# open and parse the input threagile yaml
with open(path_to_threagile_input_yaml) as existing_thrg:
    thrg_yaml_parsed = yaml.safe_load(existing_thrg)

# initialize lists to keep track of which resources have/have not been mapped
resources_not_mapped = []
resources_mapped = []

# and put all the resources in the "not mapped" list to start
for i in cf_data['Resources']:
    resources_not_mapped.append(i)

# initialize the different categories we want to capture for threagile's input
trust_boundaries = {}
technical_assets = {}
data_assets = {}
communication_links = {}

# initialize the yaml output (arguably could just overwrite the existing thrg_yaml_parsed)
yaml_output = thrg_yaml_parsed

def mark_resource_as_mapped(resource):
    '''
    function to move a resource from not_mapped to mapped
    '''
    resources_not_mapped.remove(resource)
    resources_mapped.append(resource)

def parse_cf_resources_for_trust_boundaries(cf_template):
    '''
    parses 'Resources' from cf data
    '''
    for i in cf_data['Resources']:
        # if the resource is a VPC
        aws_type = cf_data['Resources'][i]['Type']
        if aws_type in resource_rules['outer-trust-boundaries']:
            nested_boundaries = []
            # look through the other resources for subnets and keep track in a list any that are subnets in this VPC
            for j in cf_data['Resources']:
                if cf_data['Resources'][j]['Type'] in resource_rules['inner-trust-boundaries']:
                    try:
                        if cf_data['Resources'][j]['Properties']['VpcId']['Ref'] == i:
                            nested_boundaries.append(j.lower())
                    except KeyError:
                        print(j, "has no properties")
            # the nested trust boundaries that we just found will be included in the append
            trust_boundaries[i] = {
                    'id': i.lower(),
                    'aws-type': aws_type, # not needed by threagile, but useful for reference
                    'type': resource_rules['outer-trust-boundaries'][aws_type]['type'], 
                    'tags': [resource_rules['outer-trust-boundaries'][aws_type]['tags']], 
                    # 'technical_assets_inside':'', 
                    'trust_boundaries_nested': nested_boundaries
                }
            mark_resource_as_mapped(i)

        elif aws_type in resource_rules['inner-trust-boundaries']:
            # if the resource is a subnet, then just add it as a trust boundary with no nested boundaries
            trust_boundaries[i] = {
                    'id': i.lower(), 
                    'aws-type': aws_type, # not needed by threagile, but useful for reference
                    'type': resource_rules['inner-trust-boundaries'][aws_type]['type'], 
                    'tags': [resource_rules['inner-trust-boundaries'][aws_type]['tags']]
                    # 'technical_assets_inside':'', 
                    # 'trust_boundaries_nested':''
                }
            mark_resource_as_mapped(i)

def parse_cf_resources_for_technical_assets(cf_template):
    # means we're trawling the template a few times, but just a bit easier for now cos we want to
    # add references to trust boundaries, and it's easier if we've already found them all
    for i in cf_data['Resources']:
        aws_type = cf_data['Resources'][i]['Type']
        if aws_type in resource_rules['technical-assets']:
            technical_assets[i] = {
                'id': i.lower(),
                'aws-type': aws_type, # not needed by threagile, but useful for reference
                'type': resource_rules['technical-assets'][aws_type]['type'], # values: external-entity, process, datastore
                'usage': resource_rules['technical-assets'][aws_type]['usage'], # values: business, devops
                'size': resource_rules['technical-assets'][aws_type]['size'], # values: system, service, application, component
                'technology': resource_rules['technical-assets'][aws_type]['technology'], # values: see help
                'machine': resource_rules['technical-assets'][aws_type]['machine'], # values: physical, virtual, container, serverless
                'encryption': 'none', # values: none, transparent, data-with-symmetric-shared-key, data-with-asymmetric-shared-key, data-with-enduser-individual-key
                'confidentiality': 'confidential', # values: public, internal, restricted, confidential, strictly-confidential
                'integrity': 'critical', # values: archive, operational, important, critical, mission-critical
                'availability': 'critical', # values: archive, operational, important, critical, mission-critical
                'tags': [resource_rules['technical-assets'][aws_type]['tags']]
            }
            mark_resource_as_mapped(i)
            try:
                for j in cf_data['Resources'][i]['Properties']:
                    # check for references to trust boundaries and add them as links if found
                    if 'Ref' in str(cf_data['Resources'][i]['Properties'][j]):
                        # just used lower() here because we use the lowercase earlier for the id...
                        # probably better to reference the actual id of the trust boundary that we defined earlier
                        # but I just want to get this working lol...
                        dict_temp = {'technical_assets_inside': [i.lower()]}
                        if cf_data['Resources'][i]['Properties'][j]['Ref'] in trust_boundaries:
                            trust_boundaries[cf_data['Resources'][i]['Properties'][j]['Ref']].update(dict_temp)
            except KeyError:
                print(i, "has no properties")

def parse_for_communication_links(cf_template):
    # trawling the template again, but it's just a bit easier logically, since we already have the technical assets to start
    # if trawling multiplte times has a substantial performance impact then we can optimize later, but I think it's probably fine
    for i in cf_data['Resources']:
        aws_type = cf_data['Resources'][i]['Type']
        links = {'communication_links': {}}
        if aws_type in resource_rules['technical-assets']:
            if 'can_communicate_with' in resource_rules['technical-assets'][aws_type]:
                # print(resource_rules['technical-assets'][aws_type]['can_communicate_with'])
                for j in technical_assets:
                    asset_type = technical_assets[j]['aws-type']
                    if asset_type in resource_rules['technical-assets'][aws_type]['can_communicate_with']:
                        property_name = resource_rules['technical-assets'][aws_type]['can_communicate_with'][asset_type]['property_name']
                        property_name_nested =  resource_rules['technical-assets'][aws_type]['can_communicate_with'][asset_type]['property_name_nested']
                        print(property_name)
                        # property_name = cf_data['Resources'][j]['Properties'][aws_type][property_name]
                        try:
                            if type(cf_data['Resources'][i]['Properties'][property_name][property_name_nested]) is list:
                                link_target = cf_data['Resources'][i]['Properties'][property_name][property_name_nested][0].lower()
                            else:
                                link_target = cf_data['Resources'][i]['Properties'][property_name][property_name_nested].lower()
                            print("link target is: ", link_target)
                            link_name = 'Link to ' + link_target
                            link = {link_name: {
                                'target': link_target,
                                'protocol': 'https',
                                'authentication': 'none',
                                'authorization': 'none',
                                'usage': 'business'
                                    }
                                }
                            links['communication_links'].update(link)
                            
                            # add the link to the asset
                            technical_assets[i].update(links)
                        except Exception as e: print("error occured: ", repr(e), "j value: ", j, "i value: ", i, "property_name_nested: ", property_name_nested)

# run the parser functions and print out the status 
# (maybe better to use logging, but print is fine for now)
print("parsing CF template for trust boundaries")
parse_cf_resources_for_trust_boundaries(cf_data)

print("parsing CF template for trust technical assets")
parse_cf_resources_for_technical_assets(cf_data)

print("parsing CF template for communication links")
parse_for_communication_links(cf_data)


# if the existing yaml was empty for the parts we're going to add to, then initialize them
if yaml_output['technical_assets'] is None:
    yaml_output['technical_assets'] = {}

if yaml_output['trust_boundaries'] is None:
    yaml_output['trust_boundaries'] = {}


# add the things that we've translated to the output dict
print("adding parsed trust boundaries to parsed threagile yaml input")
yaml_output['trust_boundaries'].update(trust_boundaries)

print("adding parsed technical assets to parsed threagile yaml input")
yaml_output['technical_assets'].update(technical_assets)

# add the declared tags from the rules to the output dict
yaml_output['tags_available'] = sorted(list(set(yaml_output['tags_available'] + resource_rules['tags-available'])))

with open(path_to_threagile_output_yaml, 'w') as output:
    # will print with the same ordering of root elements
    # not needed per yaml spec, but nicer for readability
    print("writing updated threagile yaml to output file")
    for i in yaml_output:
        print(yaml.dump({i: yaml_output[i]}, default_flow_style=False), file=output)

for i in trust_boundaries:
    print(i)
for i in technical_assets:
    print(i)
for i in data_assets:
    print(i)
for i in communication_links:
    print(i)
print("\n")

with open("report.txt", 'w') as report:
    # write out which resources were mapped, and which weren't
    print("resources mapped", resources_mapped, file=report)
    print("resources not mapped", resources_not_mapped, file=report)

print("done")