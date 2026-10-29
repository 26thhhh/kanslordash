from kanslordash.ui.screens.server_form import AddServerScreen
from kanslordash.models import Server


def test_add_server_form_instantiates():
    screen = AddServerScreen()
    assert hasattr(screen, '_submit')
    assert hasattr(screen, 'action_save')


def test_edit_server_form_instantiates_with_key():
    server = Server(name="test", host="10.0.0.1", ssh_key_path="/tmp/nonexistent_test_key_12345")
    screen = AddServerScreen(server)
    assert screen.existing is server
    assert screen.existing.ssh_key_path != ""
