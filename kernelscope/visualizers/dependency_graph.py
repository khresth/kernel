"""
Dependency graph visualization using networkx and Plotly.
"""

import networkx as nx
import plotly.graph_objects as go
from typing import List, Dict, Any, Set, Tuple
from ..parsers.base_parser import LogEvent


class DependencyGraphVisualizer:
    """Creates dependency graph visualizations for modules and subsystems."""

    def __init__(self, events: List[LogEvent]):
        """
        Initialize dependency graph visualizer.

        Args:
            events: List of parsed log events
        """
        self.events = events
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self) -> None:
        """Build dependency graph from events."""
        subsystems = set(e.subsystem for e in self.events)
        for subsystem in subsystems:
            self.graph.add_node(subsystem, node_type="subsystem", size=20)

        drivers = set(e.driver for e in self.events if e.driver)
        for driver in drivers:
            self.graph.add_node(driver, node_type="driver", size=10)

        events_with_time = [e for e in self.events if e.timestamp is not None]
        events_with_time.sort(key=lambda x: x.timestamp)

        for event in events_with_time:
            if event.driver and event.subsystem:
                if not self.graph.has_edge(event.driver, event.subsystem):
                    self.graph.add_edge(event.driver, event.subsystem, 
                                      edge_type="belongs_to")

        subsystem_sequence = []
        for event in events_with_time:
            if event.subsystem and event.subsystem not in subsystem_sequence:
                subsystem_sequence.append(event.subsystem)

        for i in range(len(subsystem_sequence) - 1):
            if not self.graph.has_edge(subsystem_sequence[i], subsystem_sequence[i + 1]):
                self.graph.add_edge(subsystem_sequence[i], subsystem_sequence[i + 1],
                                  edge_type="init_order")

    def create_plotly_graph(self, layout: str = "spring") -> go.Figure:
        """
        Create an interactive Plotly graph visualization.

        Args:
            layout: Graph layout algorithm (spring, circular, kamada_kawai, random)

        Returns:
            Plotly figure object
        """
        if self.graph.number_of_nodes() == 0:
            fig = go.Figure()
            fig.update_layout(
                title="Dependency Graph",
                template="plotly_dark",
                annotations=[dict(text="No nodes to display", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False)]
            )
            return fig

        if layout == "spring":
            pos = nx.spring_layout(self.graph, k=1, iterations=50)
        elif layout == "circular":
            pos = nx.circular_layout(self.graph)
        elif layout == "kamada_kawai":
            pos = nx.kamada_kawai_layout(self.graph)
        else:
            pos = nx.random_layout(self.graph)

        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []

        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)

            node_type = self.graph.nodes[node].get("node_type", "unknown")
            if node_type == "subsystem":
                node_colors.append("#3B82F6")
                node_sizes.append(30)
            elif node_type == "driver":
                node_colors.append("#10B981")
                node_sizes.append(15)
            else:
                node_colors.append("#6B7280")
                node_sizes.append(10)

        edge_x = []
        edge_y = []

        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1, color="#6B7280"),
            hoverinfo="none",
            name="edges"
        ))

        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color="white")
            ),
            text=node_text,
            textposition="middle center",
            textfont=dict(size=8, color="white"),
            hovertemplate="<b>%{text}</b><extra></extra>",
            name="nodes"
        ))

        fig.update_layout(
            title=f"Dependency Graph ({layout} layout)",
            showlegend=False,
            hovermode="closest",
            template="plotly_dark",
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=600
        )

        return fig

    def get_critical_path(self) -> List[str]:
        """
        Find the critical initialization path.

        Returns:
            List of node names in critical path
        """
        if self.graph.number_of_nodes() == 0:
            return []

        try:
            longest_path = nx.dag_longest_path(self.graph)
            return longest_path
        except nx.NetworkXError:
            try:
                return list(nx.topological_sort(self.graph))
            except nx.NetworkXError:
                return []

    def get_node_centrality(self) -> Dict[str, float]:
        """
        Calculate betweenness centrality for all nodes.

        Returns:
            Dictionary mapping node names to centrality scores
        """
        return nx.betweenness_centrality(self.graph)

    def get_connected_components(self) -> List[List[str]]:
        """
        Get connected components in the graph.

        Returns:
            List of component node lists
        """
        return [list(comp) for comp in nx.weakly_connected_components(self.graph)]

    def create_centrality_chart(self) -> go.Figure:
        """
        Create a bar chart showing node centrality.

        Returns:
            Plotly figure object
        """
        centrality = self.get_node_centrality()
        if not centrality:
            fig = go.Figure()
            fig.update_layout(
                title="Node Centrality",
                template="plotly_dark",
                annotations=[dict(text="No data available", xref="paper", yref="paper",
                                x=0.5, y=0.5, showarrow=False)]
            )
            return fig

        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:20]

        fig = go.Figure(data=[go.Bar(
            x=[node for node, _ in sorted_nodes],
            y=[cent for _, cent in sorted_nodes],
            marker_color="#3B82F6"
        )])

        fig.update_layout(
            title="Node Betweenness Centrality (Top 20)",
            xaxis_title="Node",
            yaxis_title="Centrality Score",
            template="plotly_dark",
            height=500,
            xaxis=dict(tickangle=45)
        )

        return fig

    def create_module_dependency_tree(self) -> str:
        """
        Create a text-based tree representation of module dependencies.

        Returns:
            String representation of dependency tree
        """
        lines = []
        components = self.get_connected_components()

        for i, component in enumerate(components, 1):
            lines.append(f"Component {i}:")

            sorted_nodes = sorted(component,
                                key=lambda x: self.graph.in_degree(x))

            for node in sorted_nodes:
                indent = "  " * self.graph.in_degree(node)
                node_type = self.graph.nodes[node].get("node_type", "unknown")
                lines.append(f"{indent}- {node} ({node_type})")

                for successor in self.graph.successors(node):
                    if successor in component:
                        lines.append(f"{indent}  -> {successor}")

            lines.append("")

        return "\n".join(lines)

"""
Dependency graph visualizer module for creating interactive network visualizations of module and subsystem relationships.
"""
