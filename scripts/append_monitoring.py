import os
src = "/Users/joshuadavis/NISA/nisa-ui/src/components/Security.jsx"
content = open(src).read()
if "function MonitoringPanel" in content:
    print("Already present")
else:
    comp = open("/Users/joshuadavis/NISA/scripts/mon.jsx").read()
    open(src, "w").write(content.rstrip() + chr(10) + comp)
    print("Done:", "function MonitoringPanel" in open(src).read())
