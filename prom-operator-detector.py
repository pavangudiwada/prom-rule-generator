from kubernetes import client, config

rule_selectors = {} # Collects all the Prometheus Operators and their rule selectors as a dictonary with (namespace, name), a tuple as the key

def list_all_namespaces():

    config.load_kube_config()
    v1 = client.CoreV1Api()
    namespaces = v1.list_namespace() # Get all the namespaces

    return [namespace.metadata.name for namespace in namespaces.items] # For each namespaces in the list of namespaces get the name found in metadata.name


def get_prometheus_rule_selector(namespaces):
    custom_objects_api = client.CustomObjectsApi()

    for namespace in namespaces: # Get the list of namespaces and try to find a prometheus operator 
        try: # This is like running kubectl get prometheuses
            prometheus_operators = custom_objects_api.list_namespaced_custom_object( 
                group="monitoring.coreos.com",
                version="v1",
                namespace=namespace,
                plural="prometheuses"
            )

            for item in prometheus_operators['items']: # There could be multiple operators, and items has a list of them
                print(item)
                name = item['metadata']['name']        # From the metadata part of each item, get its name
                rule_selector = item.get('spec', {}).get('ruleSelector', {})   # If spec or ruleSelector doesnt exist then {} is used instead of an exception
                rule_selectors[(namespace, name)] = rule_selector     # If there was a rule add it to the rule_selector dictonary

        except client.exceptions.ApiException as e:
            print(f"An error occurred in namespace {namespace}: {e}")

    return rule_selectors

namespaces = list_all_namespaces()

rule_selectors = get_prometheus_rule_selector(namespaces)
for (namespace, name), selector in rule_selectors.items():
    print(f"Namespace: {namespace}, Operator: {name}, Rule Selector: {selector}")
