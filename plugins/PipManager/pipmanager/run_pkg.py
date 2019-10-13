import json
import pkg_resources
import sys
pkg_resources._initialize_master_working_set()
distributions = {
    dist.key: {
        "project_name": dist.project_name,
        "key": dist.key,
        "location": dist.location,
        "version": dist.version,
    }
    for dist in pkg_resources.working_set
}

package_path = sys.argv[1]

with open(package_path,"w") as f:
    json.dump(distributions,f,indent=4)