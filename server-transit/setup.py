from setuptools import setup

import versioneer

commands = versioneer.get_cmdclass()

setup(name="magic-wormhole-transit-server",
      version=versioneer.get_version(),
      description="magic-wormhole transit server",
      author="Brian Warner",
      author_email="warner-magic-wormhole@lothar.com",
      license="MIT",
      url="https://github.com/warner/magic-wormhole",
      package_dir={"": "src"},
      packages=["wormhole_transit_server",
                "wormhole_transit_server.test",
                ],
      package_data={"wormhole_transit_server": ["db-schemas/*.sql"]},
      entry_points={
          "console_scripts":
          [
              "wormhole-transit-server = wormhole_transit_server.cli:server",
          ]
      },
      install_requires=[
          "six",
          "twisted[tls] >= 17.5.0", # 17.5.0 adds failAfterFailures=
          "click",
          "humanize",
      ],
      extras_require={
          ':sys_platform=="win32"': ["pypiwin32"],
          "dev": ["mock", "tox", "pyflakes"],
      },
      test_suite="wormhole_transit_server.test",
      cmdclass=commands,
      )
