# Retrospective

A bunch of thoughts regarding choices made while working on this project.

* It would be faster to accomplish with tools available out of the box (this refers to use of cilium, locally running ollama, etc). So, I did that to try new tools, not because it provided some sort of benefit in this setup (well, not saying that it didn't).
* Trying to fit the model in the VRAM was tiresome. At first, I tried effective `gemma4` models, but they refused to work with tools. Eventually landed on `granite4.1`. Total VRAM usage with the given quantizer and 32K context is ~13GiB.
* Docs for agentgateway are a bit strange. https://agentgateway.dev/docs/kubernetes/ shows the 2.2.x version as available, but selecting it breaks page formatting a bit. Also, the latest stable version is 1.1 and the latest release on GitHub is v1.2.0-alpha.2. That's odd.
* There is another page in the agentgateway docs - https://agentgateway.dev/docs/standalone/latest/integrations/web-uis/kagent/. It tries to provide a guide for **kagent** deployment in k8s. Yet, it is located in the docs for standalone agentgateway deployment and proposes agentgateway deployment using a standard Deployment resource. That's odd and makes little sense.
* Kagent UI simply doesn't let me view agent configuration or add a new agent, throwing a generic next.js(?) error instead.
