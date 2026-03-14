import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch import models
from tests.factories import BoxFactory
from tests.factories import BoxItemFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_boxes(insert_users_for_login):
    """Create test boxes with items using factories."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        box1 = BoxFactory(name='Kitchen Stuff', number=1, size='Large', essential=True)
        BoxItemFactory(name='Plates', box=box1, essential=True)
        BoxItemFactory(name='Cups', box=box1)
        box2 = BoxFactory(name='Books', number=2, size='Book')
        BoxItemFactory(name='Python Cookbook', box=box2)
        BoxFactory(name='Empty Box', number=3, size='Small')
        session.commit()
        clear_factory_session()

    yield

    with create_session(test_settings) as session:
        session.execute(delete(models.BoxItem))
        session.execute(delete(models.Box))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_boxes, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/box-packing/')


def _get_box_from_db(name: str) -> models.Box:
    with create_session(test_settings) as session:
        return session.execute(select(models.Box).where(models.Box.name == name)).scalar_one()


def _get_box_by_id_from_db(box_id: int) -> models.Box:
    with create_session(test_settings) as session:
        return session.execute(select(models.Box).where(models.Box.id == box_id)).scalar_one()


def _box_exists_in_db(box_id: int) -> bool:
    with create_session(test_settings) as session:
        return session.execute(select(models.Box).where(models.Box.id == box_id)).scalar_one_or_none() is not None


def _get_item_from_db(name: str) -> models.BoxItem:
    with create_session(test_settings) as session:
        return session.execute(select(models.BoxItem).where(models.BoxItem.name == name)).scalar_one()


def _item_exists_in_db(item_id: int) -> bool:
    with create_session(test_settings) as session:
        return session.execute(select(models.BoxItem).where(models.BoxItem.id == item_id)).scalar_one_or_none() is not None


def test_box_packing_index(page: Page):
    expect(page).to_have_title('Box Packing')


def test_select_box(page: Page):
    """Select a box from the dropdown, verify its details appear."""
    box = _get_box_from_db('Kitchen Stuff')

    page.locator('#selected_box_id').select_option(str(box.id))
    # The select triggers form submit via JS, wait for navigation
    page.wait_for_load_state('networkidle')

    expect(page.locator('.packed-box__title')).to_contain_text('Kitchen Stuff')
    # Should show the box's items
    expect(page.locator('h3', has_text='Plates')).to_be_visible()
    expect(page.locator('h3', has_text='Cups')).to_be_visible()


def test_add_box(page: Page):
    """Add a new box via the all-boxes page form, verify in DB."""
    page.goto(f'{FRONTEND_BASE_URL}/box-packing/all/')

    form = page.locator('form.add-item-form')
    form.locator('#box_name').fill('Playwright Box')
    form.locator('#box_number').fill('99')
    form.locator('#box_size').select_option('Medium')
    form.locator('#essential').check()
    form.locator('button[value="add_box"]').click()

    box = _get_box_from_db('Playwright Box')
    assert box.number == 99
    assert box.size == 'Medium'
    assert box.essential is True
    assert box.warm is not True
    assert box.liquid is not True


def test_edit_box(page: Page):
    """Edit a box via the edit page, verify changes persist in DB."""
    box = _get_box_from_db('Kitchen Stuff')
    box_id = box.id

    page.goto(f'{FRONTEND_BASE_URL}/box-packing/edit/{box_id}/')
    expect(page).to_have_title('Edit Box')

    form = page.locator('form.add-item-form')
    form.locator('#box_name').fill('Updated Kitchen')
    form.locator('#box_size').select_option('Small')
    form.locator('button[value="edit_box"]').click()

    result = _get_box_by_id_from_db(box_id)
    assert result.name == 'Updated Kitchen'
    assert result.size == 'Small'
    assert result.number == 1, 'Number should survive edit'


def test_add_item_to_box(page: Page):
    """Select a box, add an item via the form, verify in DB."""
    box = _get_box_from_db('Empty Box')

    # Navigate to the box's detail view
    page.goto(f'{FRONTEND_BASE_URL}/box-packing/{box.id}/')

    form = page.locator('form.add-item-form')
    form.locator('#item_name').fill('New Widget')
    form.locator('#essential').check()
    form.locator('button[value="add_item"]').click()

    item = _get_item_from_db('New Widget')
    assert item.box_id == box.id
    assert item.essential is True


def test_delete_item(page: Page):
    """Delete an item from a box, verify gone from DB."""
    item = _get_item_from_db('Cups')
    item_id = item.id
    box = _get_box_from_db('Kitchen Stuff')

    page.goto(f'{FRONTEND_BASE_URL}/box-packing/{box.id}/')

    # Target the delete button in the item's form
    item_form = page.locator(f'form:has(input[name="item_id"][value="{item_id}"])')
    item_form.locator('button[value="delete_item"]').click()

    assert not _item_exists_in_db(item_id), 'Item should be deleted'


def test_delete_box(page: Page):
    """Delete a box, verify gone from DB."""
    box = _get_box_from_db('Empty Box')
    box_id = box.id

    page.goto(f'{FRONTEND_BASE_URL}/box-packing/{box_id}/')

    page.locator('button[value="delete_box"]').click()

    assert not _box_exists_in_db(box_id), 'Box should be deleted'


def test_box_create_add_items_edit_lifecycle(page: Page):
    """Create a box, add items, edit the box, verify accumulated state."""
    # Create box on the all-boxes page
    page.goto(f'{FRONTEND_BASE_URL}/box-packing/all/')
    form = page.locator('form.add-item-form')
    form.locator('#box_name').fill('Lifecycle Box')
    form.locator('#box_number').fill('50')
    form.locator('#box_size').select_option('Large')
    form.locator('button[value="add_box"]').click()

    box = _get_box_from_db('Lifecycle Box')
    box_id = box.id

    # Add an item
    page.goto(f'{FRONTEND_BASE_URL}/box-packing/{box_id}/')
    add_form = page.locator('form.add-item-form')
    add_form.locator('#item_name').fill('Lifecycle Item')
    add_form.locator('#essential').check()
    add_form.locator('button[value="add_item"]').click()

    item = _get_item_from_db('Lifecycle Item')
    assert item.box_id == box_id
    assert item.essential is True

    # Edit the box
    page.goto(f'{FRONTEND_BASE_URL}/box-packing/edit/{box_id}/')
    edit_form = page.locator('form.add-item-form')
    edit_form.locator('#box_name').fill('Lifecycle Box Renamed')
    edit_form.locator('#box_size').select_option('Small')
    edit_form.locator('button[value="edit_box"]').click()

    result = _get_box_by_id_from_db(box_id)
    assert result.name == 'Lifecycle Box Renamed'
    assert result.size == 'Small'
    assert result.number == 50, 'Number should survive edit'

    # Verify item still belongs to the box
    item_after = _get_item_from_db('Lifecycle Item')
    assert item_after.box_id == box_id, 'Item should still be in the box after edit'
