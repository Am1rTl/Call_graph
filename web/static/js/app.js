const app = new Vue({
    el: '#app',
    data: {
        viewMode: 'cytoscape',
        graphData: { nodes: [], edges: [] },
        file: null
    },
    methods: {
        handleFileUpload(event) {
            this.file = event.target.files[0];
        },
        parseCode() {
            const formData = new FormData();
            formData.append('file', this.file);

            fetch('/parse', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    this.graphData = data;
                    this.renderGraph();
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        },
        renderGraph() {
            if (this.viewMode === 'cytoscape') {
                this.renderCytoscape();
            } else {
                this.renderFlyPie();
            }
        },
        renderCytoscape() {
            const cy = cytoscape({
                container: document.getElementById('cytoscape-container'),
                elements: {
                    nodes: this.graphData.nodes.map(node => ({ data: { id: node.id } })),
                    edges: this.graphData.edges.map(edge => ({
                        data: { source: edge.source, target: edge.target }
                    }))
                },
                style: [
                    {
                        selector: 'node',
                        style: {
                            'label': 'data(id)',
                            'background-color': '#666',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': '#fff',
                            'font-size': '12px'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 2,
                            'line-color': '#999',
                            'curve-style': 'bezier'
                        }
                    }
                ],
                layout: {
                    name: 'breadthfirst',
                    directed: true,
                    padding: 10,
                    spacingFactor: 1.5,
                    animate: true
                }
            });
        },
        renderFlyPie() {
            const width = 800, height = 600;
            const svg = d3.select("#flypie-container")
                .html("")
                .append("svg")
                .attr("width", width)
                .attr("height", height);

            const nodes = this.graphData.nodes.map(node => node.id);
            const radius = Math.min(width, height) / 2 - 50;

            const angle = (2 * Math.PI) / nodes.length;
            const nodePositions = nodes.map((node, i) => ({
                id: node,
                x: width / 2 + radius * Math.cos(angle * i),
                y: height / 2 + radius * Math.sin(angle * i)
            }));

            // Рисуем узлы
            svg.selectAll("circle")
                .data(nodePositions)
                .enter()
                .append("circle")
                .attr("cx", d => d.x)
                .attr("cy", d => d.y)
                .attr("r", 10)
                .attr("fill", "#69b3a2");

            // Рисуем текст
            svg.selectAll("text")
                .data(nodePositions)
                .enter()
                .append("text")
                .attr("x", d => d.x + 15)
                .attr("y", d => d.y)
                .text(d => d.id)
                .attr("font-size", "12px")
                .attr("fill", "#333");

            // Рисуем ребра
            this.graphData.edges.forEach(edge => {
                const source = nodePositions.find(n => n.id === edge.source);
                const target = nodePositions.find(n => n.id === edge.target);
                if (source && target) {
                    svg.append("line")
                        .attr("x1", source.x)
                        .attr("y1", source.y)
                        .attr("x2", target.x)
                        .attr("y2", target.y)
                        .attr("stroke", "#999")
                        .attr("stroke-width", 2);
                }
            });
        }
    }
});