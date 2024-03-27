import pickle
import pyvista as pv
import tempfile
# from os import remove

from pyvista.trame.ui import plotter_ui
from trame.app import get_server
from trame.app.file_upload import ClientFile
from trame.ui.vuetify3 import SinglePageWithDrawerLayout
from trame.widgets import vuetify3

pv.OFF_SCREEN = True
# Server config
server = get_server()
server.client_type = "vue3"
state, ctrl = server.state, server.controller
# Server variables
pl = pv.Plotter()
state.setdefault("mesh", None)
state.setdefault("scalars", [])
state.setdefault("scalars_options", [])
state.setdefault(
    "styles", ["surface", "wireframe", "points", "points_gaussian"]
)


@state.change("scalar_selector", "style_selector", "show_edges")
def changeOptions(**kwargs):
    if state.mesh:
        pl.clear_actors()
        pl.add_mesh(
            pickle.loads(state.mesh),
            style=state.style_selector,
            scalars=state.scalar_selector,
            show_scalar_bar=True,
            show_edges=state.show_edges,
        )


@state.change("file_exchange")
def handleFile(file_exchange, **kwargs):
    pl.clear_actors()
    state.scalar_selector = None
    state.style_selector = None
    state.scalars_options = []
    state.mesh = None
    if file_exchange and len(file_exchange) > 0:
        file = ClientFile(file_exchange[0])
        print(file.info)
        bytes = file.content
        # Using a tempfile
        with tempfile.NamedTemporaryFile(suffix=file.name) as path:
            with open(path.name, "wb") as f:
                f.write(bytes)
            mesh = pv.read(path.name)
        '''
        # I can't make the tempfile work in Windows, so this is a suboptimal alternative to the tempfile
        tempfile = "temp-" + file.name
        with open(tempfile, 'wb') as f:
            f.write(bytes)
            mesh = pv.read(tempfile)
        remove(tempfile)
        '''
        state.mesh = pickle.dumps(mesh)
        state.scalars = mesh.array_names
        state.scalars_options = [
            {"title": option, "value": option}
            for option in state.scalars
        ]
        pl.add_mesh(mesh, show_scalar_bar=True)
    pl.reset_camera()


def build_ui():
    with SinglePageWithDrawerLayout(server) as layout:
        with layout.toolbar:
            vuetify3.VSpacer()
            vuetify3.VFileInput(
                show_size=True,
                closable_chips=True,
                truncate_length=25,
                v_model=("file_exchange", None),
                dense=True,
                hide_details=True,
                style="max-width: 300px;",
                multiple=False,
            )
            vuetify3.VProgressLinear(
                indeterminate=True,
                absolute=True,
                bottom=True,
                active=("trame__busy",),
            )
        with layout.drawer:
            with vuetify3.VRadioGroup(
                v_model=("style_selector", None), label="Style"
            ):
                for option in state.styles:
                    vuetify3.VRadio(label=option, value=option)
            vuetify3.VSelect(
                v_model=("scalar_selector", None),
                label="Scalar",
                items=("scalars_options",),
            )
            vuetify3.VSwitch(
                v_model=("show_edges", False),
                label="Show edges",
            )
        with layout.content:
            with vuetify3.VContainer(
                fluid=True,
                classes="pa-0 fill-height",
                style="position: relative;",
            ):
                view = plotter_ui(pl)
                ctrl.view_update = view.update


if __name__ == "__main__":
    build_ui()
    server.start()
