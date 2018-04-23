import csv
import logging

DEFAULT_ZIP_CODE_FILE_NAME = 'zips.csv'
DEFAULT_COVERAGE_PLAN_FILE_NAME = 'plans.csv'
DEFAULT_SLCSP_FILE_NAME = 'slcsp.csv'
DEFAULT_SLCSP_OUTPUT_FILE_NAME = 'slcsp-output.csv'

PLAN_TYPE = 'Silver'

logging.basicConfig(level=logging.INFO)


def generate_slcsp_report():
    zipcodes = ZipCodes(DEFAULT_ZIP_CODE_FILE_NAME).load()
    coverage_plans = CoveragePlans(DEFAULT_COVERAGE_PLAN_FILE_NAME).load()
    slc_silver_plan = Slcsp(DEFAULT_SLCSP_FILE_NAME, zipcodes,
                            coverage_plans).load()
    slc_silver_plan.calculate_slcsp()
    slc_silver_plan.write_slcsp(DEFAULT_SLCSP_OUTPUT_FILE_NAME)


class Slcsp():
    def __init__(self, slcsp_file_name, zipcodes, coverage_plans):
        self.slcsp_file_name = slcsp_file_name
        self.zipcodes = zipcodes
        self.coverage_plans = coverage_plans
        self.slcsp_rows = None

    def load(self, slcsp_file_name=None):
        if slcsp_file_name is not None:
            self.slcsp_file_name = slcsp_file_name

        with open(self.slcsp_file_name) as slcsp_file:
            csv_reader = csv.DictReader(slcsp_file)

            self.slcsp_rows = []

            for row in csv_reader:
                self.slcsp_rows.append(row)

        logging.info('successfully loaded slcsp zipcodes from file: {}'.format(
            self.slcsp_file_name))

        return self

    def calculate_slcsp(self):
        for slcsp_row in self.slcsp_rows:
            zip_code_rows = self.zipcodes.get_by_zipcode(slcsp_row['zipcode'])
            silver_rates = []
            initial_rate_area = None

            for zip_code_row in zip_code_rows:
                if not initial_rate_area:
                    initial_rate_area = zip_code_row['rate_area']
                elif initial_rate_area != zip_code_row['rate_area']:
                    silver_rates = []
                    logging.info(
                        'Found conflicting rate areas ({initial_rate_area}, {current_rate_area}) for same zipcode: {zipcode}'.
                        format(
                            initial_rate_area=initial_rate_area,
                            current_rate_area=zip_code_row['rate_area'],
                            zipcode=slcsp_row['zipcode']))
                    break

                coverage_plan_rows = self.coverage_plans.get_by_state_rate_area(
                    zip_code_row['state'], zip_code_row['rate_area'])
                for coverage_plan_row in coverage_plan_rows:
                    if coverage_plan_row['metal_level'] == PLAN_TYPE:
                        silver_rates.append(float(coverage_plan_row['rate']))

            if not zip_code_rows:
                logging.info('Could not find any data for zipcode: {}'.format(
                    slcsp_row['zipcode']))

            if not silver_rates:
                logging.info(
                    'Could not find any silver rates for zipcode: {}'.format(
                        slcsp_row['zipcode']))

            if len(silver_rates):
                silver_rates = sorted(set(silver_rates))
                if len(silver_rates) == 1:
                    slcsp_row['rate'] = silver_rates[0]
                else:
                    slcsp_row['rate'] = silver_rates[1]

        logging.info('successfully calculated slcsp for zipcodes')

    def write_slcsp(self, slcsp_output_file_name):
        with open(slcsp_output_file_name, 'w') as slcsp_output_file:
            field_names = ['zipcode', 'rate']
            csv_writer = csv.DictWriter(
                slcsp_output_file, fieldnames=field_names)
            csv_writer.writeheader()
            for slcsp_row in self.slcsp_rows:
                csv_writer.writerow(slcsp_row)

            logging.info('successfully wrote slcsp to file {}'.format(
                slcsp_output_file_name))


class ZipCodes():
    def __init__(self, zip_code_file_name):
        self.zip_code_file_name = zip_code_file_name
        self.zip_code_mapping = None

    def load(self, zip_code_file_name=None):
        if zip_code_file_name is not None:
            self.zip_code_file_name = zip_code_file_name

        with open(self.zip_code_file_name) as zip_code_file:
            csv_reader = csv.DictReader(zip_code_file)

            self.zip_code_mapping = {}

            for row in csv_reader:
                if not row['zipcode'] in self.zip_code_mapping:
                    self.zip_code_mapping[row['zipcode']] = []

                self.zip_code_mapping[row['zipcode']].append(row)

        logging.info('successfully loaded zipcode data from file: {}'.format(
            self.zip_code_file_name))

        return self

    def get_by_zipcode(self, zipcode):
        if zipcode not in self.zip_code_mapping:
            return []
        return self.zip_code_mapping[zipcode]


class CoveragePlans():
    def __init__(self, coverage_plan_file_name):
        self.coverage_plan_file_name = coverage_plan_file_name
        self.coverage_plan_mapping = None

    def load(self, coverage_plan_file_name=None):
        if coverage_plan_file_name is not None:
            self.coverage_plan_file_name = coverage_plan_file_name

        with open(self.coverage_plan_file_name) as coverage_plan_file:
            csv_reader = csv.DictReader(coverage_plan_file)

            self.coverage_plan_mapping = {}

            for row in csv_reader:
                rate_area_tuple = row['state'] + ' ' + row['rate_area']

                if rate_area_tuple not in self.coverage_plan_mapping:
                    self.coverage_plan_mapping[rate_area_tuple] = []

                self.coverage_plan_mapping[rate_area_tuple].append(row)

            logging.info(
                'successfully loaded coverage plan data from file: {}'.format(
                    self.coverage_plan_file_name))

        return self

    def get_by_state_rate_area(self, state, rate_area):
        rate_area_tuple = state + ' ' + rate_area

        if rate_area_tuple not in self.coverage_plan_mapping:
            return []

        return self.coverage_plan_mapping[rate_area_tuple]


# Generates the report when you import the file
# makes it easier to run from command line
generate_slcsp_report()
