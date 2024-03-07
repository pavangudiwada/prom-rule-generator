import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_all_namespaces(v1_client):
    try:
        namespaces = v1_client.list_namespace() 
    
    except Exception as e:
        logging.error(f"An error occured while detecting namespaces: {e}")

    logging.info("Sending namespace info")
    return [namespace.metadata.name for namespace in namespaces.items] # For each namespaces in the list of namespaces get the name found in metadata.name

def get_all_prometheuses(namespaces, custom_objects_client):
    
    all_prometheus = []
    for namespace in namespaces:
        try:
            prometheus_crs = custom_objects_client.list_namespaced_custom_object(
                group="monitoring.coreos.com",
                version="v1",
                namespace=namespace,
                plural="prometheuses"
            )
            if prometheus_crs['items']:
                all_prometheus.append(prometheus_crs['items'])

        except Exception as e:
            logging.error(f"An error occurred in namespace {namespace}: {e}")
            return []

    return all_prometheus




def get_prometheus_rule_selector(namespaces, custom_objects_client):
    rule_selectors = {} # Collects all the Prometheuses and their rule selectors as a set (namespace, name)
    rule_namespace_selector = {}
    for namespace in namespaces: # Get the list of namespaces and try to find a prometheus
        try: # This is like running kubectl get prometheuses
            prometheus_instances = custom_objects_api.list_namespaced_custom_object( 
                group="monitoring.coreos.com",
                version="v1",
                namespace=namespace,
                plural="prometheuses"
            )

            for item in prometheus_instances['items']: # There could be multiple prometheuses, and items has a list of them
                name = item['metadata']['name']        # From the metadata part of each item, get its name
                rule_selector = item.get('spec', {}).get('ruleSelector', {})   # If spec or ruleSelector doesnt exist then {} is used instead of an exception
                rule_selectors[(namespace, name)] = rule_selector     # If there was a rule 

                rule_namespace = item.get('spec', {}).get('ruleNamespaceSelector', {})
                rule_namespace_selector[(namespace, name)] = rule_namespace

        except client.exceptions.ApiException as e:
            logging.warning(f"An error occurred in namespace {namespace}: {e}")

    return rule_selectors, rule_namespace_selector

def get_namespace_labels(v1_client, namespace):
    try:
        ns = v1_client.read_namespace(name=namespace)
        return ns.metadata.labels
    except client.exceptions.ApiException as e:
        logging.warning(f"An error occurred: {e}")
        return None


def get_all_namespace_labels(v1_client, namespaces):
    try:
        all_labels = {}
        for namespace in namespaces:
            ns_labels = get_namespace_labels(v1_client, namespace)
            if ns_labels:
                all_labels.update(ns_labels)
        return all_labels
    except Exception as e:
        logging.error(f"Exception {e} occured while getting all namespace labels")


def get_prometheus_selectors(v1_client, namespace, prometheus):
    namespace_labels = {}
    rule_labels = {}
    no_ns_label = {}

    try:
        rule_labels = prometheus[0].get('spec', {}).get('ruleSelector', {})
        namespace_labels = prometheus[0].get('spec', {}).get('ruleNamespaceSelector', {})
        if rule_labels:
            rule_labels = rule_labels["matchLabels"]
        if namespace_labels:
            inner_dict = namespace_labels.get('matchLabels', {})
            if inner_dict:
                namespace_labels = {"namespace": next(iter(inner_dict.values()), None)}

                all_labels = get_all_namespace_labels(v1_client)

                if inner_dict.items() not in all_labels.items():
                    no_ns_label = inner_dict
            else:
                logging.info("No namespace labels")

    except Exception as e:
        logging.error(f"An error {e} occured while getting Prometheus selectors")
    
    return namespace_labels, rule_labels, no_ns_label