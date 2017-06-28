from setuptools import setup

import versioneer

commands = versioneer.get_cmdclass()

setup(name="magic-wormhole-rendezvous-server",
      version=versioneer.get_version(),
      description="magic-wormhole rendezvous server",
      author="Brian Warner",
      author_email="warner-magic-wormhole@lothar.com",
      license="MIT",
      url="https://github.com/warner/magic-wormhole",
      package_dir={"": "src"},
      packages=["wormhole_rendezvous_server",
                "wormhole_rendezvous_server.test",
                ],
      package_data={"wormhole_rendezvous_server": ["db-schemas/*.sql"]},
      entry_points={
          "console_scripts":
          [
              "wormhole-server = wormhole_rendezvous_server.cli:server",
          ]
      },
      install_requires=[
          "six",
          "twisted[tls] >= 17.5.0", # 17.5.0 adds failAfterFailures=
          "autobahn[twisted] >= 0.14.1",
          "click",
          "humanize",
      ],
      extras_require={
          ':sys_platform=="win32"': ["pypiwin32"],
          "dev": ["mock", "tox", "pyflakes"],
      },
      test_suite="wormhole_rendezvous_server.test",
      cmdclass=commands,
      )
