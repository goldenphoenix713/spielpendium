import dash
import dash_mantine_components as dmc

dash.register_page(__name__, path="/")  # type: ignore  # ty: ignore[unused-type-ignore-comment, unused-ignore-comment]

layout = dmc.Container(
    [
        dmc.Title("Welcome to Spielpendium", order=1),
        dmc.Text(
            "Navigate to the Collection page to view your board games.",
            mt="md",
        ),
    ],
    fluid=True,
)
