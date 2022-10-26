from argparse import ArgumentParser
from colorama import Fore, Back, Style
import re
import attr
import requests

# REF: https://autopilot-docs.readthedocs.io/en/latest/license_list.html

PYPI_PACKAGE_URL = 'https://pypi.python.org/pypi/{package}/json'
PYPI_PACKAGE_VERSION_URL = 'https://pypi.python.org/pypi/{package}/{version}/json'

@attr.s(kw_only=True)
class RequirementParser:
    input_file_path = attr.ib()
    
    def parse_requirements():
        raise NotImplemented()

@attr.s(kw_only=True)
class SimpleRequirementParser(RequirementParser):
    def parse_requirements(self):
        package_versions = []
        with open(self.input_file_path, 'r') as fp:
            for line in fp:
                line, __, __ = line.partition("#")
                line = line.strip()
                if line == "":
                    continue

                item = self.parse_line(line)
                package_versions.append(item)
                yield item

        return package_versions
    
    def parse_line(self, line):
        m = re.match(r"^([a-z0-9_-]+)([=<>]{0,2})([a-z0-9._-]*).*?$", line, re.I)
        if not m:
            raise Exception("Unsupported format: " + line)

        if m.group(2) == "==":
            item = (m.group(1), m.group(3))
        else:
            item = (m.group(1), None)
        
        return item



@attr.s(kw_only=True)
class Output:
    output_file_path = attr.ib(default=None)
    output_file = attr.ib(init=False)

    @output_file.default
    def _output_file(self):
        if self.output_file_path:
            return open(self.output_file_path, 'w')

    def print(self, *,msg):
        if self.output_file_path:
            self.output_file.write(f'{msg}\n')
        else:
            print(f'{msg}\n')
    
    def print_info(self, *,package, version, license):
        msg = f"{package}=={version}: {license}"
        if self.is_gpl_license(license=license):
            if self.output_file_path:
                msg = f'* {msg}'
            else:
                msg = f'{Fore.RED}{msg}'
        self.print(msg=msg)
    
    def is_gpl_license(self, *, license):
        return 'gpl' in license.lower()


@attr.s(kw_only=True)
class PYPIInfo:
    parser = attr.ib()
    output = attr.ib()
    
    def get_pypi_json(self, package, version=None):
        url = PYPI_PACKAGE_VERSION_URL
        if version is None:
            url = PYPI_PACKAGE_URL
        url = url.format(package=package, version=version)
        r = requests.get(url)
        return r.json()

    def check_license(self, package, version=None):
        pypi_json = self.get_pypi_json(package, version)
        info = pypi_json.get('info', {})
        license = info.get('license')
        license_classifier = False
        for classifier in info.get('classifiers'):
            if classifier.lower().startswith('license'):
                license_classifier = True
                license_info = f'{license} ({classifier})'
                self.output.print_info(package=package, version=version, license=license_info)
                break

        if not (license or license_classifier):
            self.output.print_info(package=package, version=version, license="UNKNOWN")

    def get_info(self):
        for package_version in self.parser.parse_requirements():
            package = package_version[0]
            version = package_version[1]
            self.check_license(package, version)


def main():
    parser = ArgumentParser('Retrieving license info from pypi')
    parser.add_argument('-i', '--input-file-path', default='requirements.txt', help='input requirement files, currently only support requirements.txt format')
    parser.add_argument('-o', '--output-file-path', help='output result to a file, default will be the console')

    args = parser.parse_args()

    input_file_path = args.input_file_path
    output_file_path = args.output_file_path
    output = Output(output_file_path=output_file_path)

    req_parser = SimpleRequirementParser(input_file_path=input_file_path)
    pypi_info = PYPIInfo(parser=req_parser, output=output)
    pypi_info.get_info()


if __name__ == '__main__':
    main()