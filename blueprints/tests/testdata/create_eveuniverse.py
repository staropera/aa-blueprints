from django.test import TestCase

from eveuniverse.tools.testdata import ModelSpec, create_testdata

from . import eveuniverse_test_data_filename


class CreateEveUniverseTestData(TestCase):
    def test_create_testdata(self):
        testdata_spec = [
            ModelSpec("EveSolarSystem", ids=[30000142, 30004984, 30001161, 30002537]),
            ModelSpec(
                "EveType",
                ids=[
                    5,
                    23,
                    603,
                    20185,
                    24311,
                    24312,
                    35832,
                    35835,
                    52678,
                ],
            ),
            ModelSpec(
                "EveType",
                ids=[
                    19540,
                    19551,
                    19553,
                    33519,
                ],
                include_children=True,
            ),
        ]
        create_testdata(testdata_spec, eveuniverse_test_data_filename())
