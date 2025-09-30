# Database schemas for StudyNet CSV data

# Table schemas for DuckDB
PROVIDERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS providers (
    provider_id VARCHAR PRIMARY KEY,
    provider_name VARCHAR,
    company_name VARCHAR,
    provider_country VARCHAR DEFAULT 'Australia',
    status VARCHAR,
    public_private VARCHAR,
    provider_type VARCHAR,
    global_ranking INTEGER,
    australian_ranking INTEGER,
    recognised_area_of_study TEXT,
    accepts_ielts BOOLEAN,
    accepts_toefl BOOLEAN,
    accepts_duolingo BOOLEAN,
    accepts_sat BOOLEAN,
    accepts_act BOOLEAN,
    website_url VARCHAR,
    scholarship_url VARCHAR,
    accommodation_url VARCHAR,
    facilities TEXT,
    has_on_campus_accommodation BOOLEAN,
    profile TEXT,
    keywords TEXT,
    is_active BOOLEAN,
    cricos_provider_code VARCHAR,
    provider_crm_id VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_provider_name ON providers(provider_name);
CREATE INDEX IF NOT EXISTS idx_australian_ranking ON providers(australian_ranking);
CREATE INDEX IF NOT EXISTS idx_provider_type ON providers(provider_type);
"""

CAMPUS_LOCATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS campus_locations (
    campus_id VARCHAR PRIMARY KEY,
    campus_name VARCHAR,
    provider_id VARCHAR,
    provider_name VARCHAR,
    address_street VARCHAR,
    address_state VARCHAR,
    state_id VARCHAR,
    address_city VARCHAR,
    city_id VARCHAR,
    address_postcode VARCHAR,
    campus_nearest_city VARCHAR,
    country_code VARCHAR,
    on_campus_accommodation BOOLEAN,
    campus_note TEXT,
    address_geocode VARCHAR,
    cricos_provider_code VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_campus_city ON campus_locations(address_city);
CREATE INDEX IF NOT EXISTS idx_campus_state ON campus_locations(address_state);
CREATE INDEX IF NOT EXISTS idx_campus_provider ON campus_locations(provider_id);
"""

COURSES_SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    course_id VARCHAR PRIMARY KEY,
    course_name VARCHAR,
    provider_id VARCHAR,
    provider_name VARCHAR,
    course_level VARCHAR,
    study_level VARCHAR,
    sub_study_level VARCHAR,
    area_of_study_broad VARCHAR,
    area_of_study_narrow VARCHAR,
    area_of_study_detailed VARCHAR,
    area_of_study_detailed_code VARCHAR,
    course_type VARCHAR,
    english_course_type VARCHAR,
    provider_course_code VARCHAR,
    description TEXT,
    duration DECIMAL,
    duration_unit VARCHAR,
    duration_ft_phrase VARCHAR,
    entry_requirements TEXT,
    is_active BOOLEAN,
    has_scholarship BOOLEAN,
    has_internship BOOLEAN,
    has_bridging_program BOOLEAN,
    work_exp VARCHAR,
    majors TEXT,
    awarding_body VARCHAR,
    -- English Requirements
    ielts_overall DECIMAL,
    ielts_reading DECIMAL,
    ielts_writing DECIMAL,
    ielts_speaking DECIMAL,
    ielts_listening DECIMAL,
    toefl_overall_ibt INTEGER,
    toefl_reading_ibt INTEGER,
    toefl_writing_ibt INTEGER,
    toefl_speaking_ibt INTEGER,
    toefl_listening_ibt INTEGER,
    toefl_overall_pbt INTEGER,
    duolingo_score INTEGER,
    pte_score INTEGER,
    -- Other scores
    atar DECIMAL,
    cae_score INTEGER,
    sat_score INTEGER,
    act_score INTEGER,
    gre_verbal_reasoning INTEGER,
    gre_quantitative_reasoning INTEGER,
    gre_analytic_writing DECIMAL,
    lsat_score INTEGER,
    -- Application fees
    application_fee_paper DECIMAL,
    application_fee_online DECIMAL,
    application_fee_currency VARCHAR,
    -- URLs
    url_course_info VARCHAR,
    url_admission_info VARCHAR,
    url_bridging_program_info VARCHAR,
    url_career_outcomes VARCHAR,
    url_orientation_info VARCHAR,
    url_pathway_info VARCHAR,
    -- Metadata
    keywords TEXT,
    department_name VARCHAR,
    professional_recognition TEXT,
    estimated_job_roles TEXT,
    cricos_code VARCHAR,
    crm_id VARCHAR,
    is_international BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_course_name ON courses(course_name);
CREATE INDEX IF NOT EXISTS idx_course_provider ON courses(provider_id);
CREATE INDEX IF NOT EXISTS idx_course_study_level ON courses(study_level);
CREATE INDEX IF NOT EXISTS idx_course_area_broad ON courses(area_of_study_broad);
CREATE INDEX IF NOT EXISTS idx_course_area_narrow ON courses(area_of_study_narrow);
CREATE INDEX IF NOT EXISTS idx_course_has_scholarship ON courses(has_scholarship);
CREATE INDEX IF NOT EXISTS idx_course_is_active ON courses(is_active);
"""

FEES_SCHEMA = """
CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY,
    provider_id VARCHAR,
    provider_name VARCHAR,
    course_id VARCHAR,
    course_name VARCHAR,
    year INTEGER,
    unit VARCHAR,
    unit_price DECIMAL,
    unit_count INTEGER,
    currency VARCHAR DEFAULT 'AUD',
    total_annual_fee DECIMAL,
    total_course_fee DECIMAL,
    fee_link VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_fee_course_id ON fees(course_id);
CREATE INDEX IF NOT EXISTS idx_fee_provider_id ON fees(provider_id);
CREATE INDEX IF NOT EXISTS idx_fee_annual_fee ON fees(total_annual_fee);
CREATE INDEX IF NOT EXISTS idx_fee_year ON fees(year);
"""

INTAKES_SCHEMA = """
CREATE TABLE IF NOT EXISTS intakes (
    intake_id VARCHAR PRIMARY KEY,
    provider_id VARCHAR,
    provider_name VARCHAR,
    year INTEGER,
    commencement_date DATE,
    end_date DATE,
    orientation_date DATE,
    application_deadline DATE,
    is_open BOOLEAN,
    tentative BOOLEAN
);

CREATE INDEX IF NOT EXISTS idx_intake_provider ON intakes(provider_id);
CREATE INDEX IF NOT EXISTS idx_intake_year ON intakes(year);
CREATE INDEX IF NOT EXISTS idx_intake_is_open ON intakes(is_open);
"""

# CSV column mappings (CSV header → Database column)
PROVIDERS_COLUMN_MAP = {
    'PROVIDERID': 'provider_id',
    'PROVIDERNAME': 'provider_name',
    'COMPANYNAME': 'company_name',
    'PROVIDERCOUNTRY': 'provider_country',
    'STATUS': 'status',
    'PUBLICPRIVATE': 'public_private',
    'PROVIDERTYPE': 'provider_type',
    'GLOBALRANKING': 'global_ranking',
    'AUSTRALIANRANKING': 'australian_ranking',
    'RECOGNISEDAREAOFSTUDY': 'recognised_area_of_study',
    'ACCEPTSIELTS': 'accepts_ielts',
    'ACCEPTSTOEFL': 'accepts_toefl',
    'ACCEPTSDUOLINGO': 'accepts_duolingo',
    'ACCEPTSSAT': 'accepts_sat',
    'ACCEPTSACT': 'accepts_act',
    'WEBSITEURL': 'website_url',
    'SCHOLARSHIPS': 'scholarship_url',
    'ACCOMMODATION': 'accommodation_url',
    'FACILITIES': 'facilities',
    'HASONCAMPUSACCOMMODATION': 'has_on_campus_accommodation',
    'PROFILE': 'profile',
    'KEYWORDS': 'keywords',
    'ISACTIVE': 'is_active',
    'CRICOSPROVIDERCODE': 'cricos_provider_code',
    'ProviderCRMID': 'provider_crm_id'
}

CAMPUS_LOCATIONS_COLUMN_MAP = {
    'CAMPUSID': 'campus_id',
    'CAMPUSNAME': 'campus_name',
    'PROVIDERID': 'provider_id',
    'ProviderName': 'provider_name',
    'ADDRESSSTREET': 'address_street',
    'ADDRESSSTATE': 'address_state',
    'StateId': 'state_id',
    'ADDRESSCITY': 'address_city',
    'CityId': 'city_id',
    'ADDRESSPOSTCODE': 'address_postcode',
    'CAMPUSNEARESTCITY': 'campus_nearest_city',
    'CountryCode': 'country_code',
    'ONCAMPUSACCOMMODATION': 'on_campus_accommodation',
    'CAMPUSNOTE': 'campus_note',
    'ADDRESSGEOCODE': 'address_geocode',
    'PROVIDERCRICOSCODE': 'cricos_provider_code'
}

COURSES_COLUMN_MAP = {
    'COURSEID': 'course_id',
    'COURSENAME': 'course_name',
    'PROVIDERID': 'provider_id',
    'ProviderName': 'provider_name',
    'COURSELEVEL': 'course_level',
    'STUDYLEVEL': 'study_level',
    'SUBSTUDYLEVEL': 'sub_study_level',
    'AREAOFSTUDYBROAD': 'area_of_study_broad',
    'AREAOFSTUDYNARROW': 'area_of_study_narrow',
    'AREAOFSTUDYDETAILED': 'area_of_study_detailed',
    'AREAOFSTUDYDETAILEDCODE': 'area_of_study_detailed_code',
    'COURSETYPE': 'course_type',
    'ENGLISHCOURSETYPE': 'english_course_type',
    'PROVIDERCOURSECODE': 'provider_course_code',
    'Description': 'description',
    'Duration': 'duration',
    'DurationUnit': 'duration_unit',
    'DURATIONFTPHRASE': 'duration_ft_phrase',
    'ENTRYREQUIREMENTS': 'entry_requirements',
    'ISACTIVE': 'is_active',
    'HASSCHOLARSHIP': 'has_scholarship',
    'HASINTERNSHIP': 'has_internship',
    'HASBRIDGINGPROGRAM': 'has_bridging_program',
    'WORKEXP': 'work_exp',
    'MAJORS': 'majors',
    'AWARDINGBODY': 'awarding_body',
    'IELTSOVERALL': 'ielts_overall',
    'IELTSREADING': 'ielts_reading',
    'IELTSWRITING': 'ielts_writing',
    'IELTSSPEAKING': 'ielts_speaking',
    'IELTSLISTENING': 'ielts_listening',
    'TOEFLOVERALLIBT': 'toefl_overall_ibt',
    'TOEFLREADINGIBT': 'toefl_reading_ibt',
    'TOEFLWRITINGIBT': 'toefl_writing_ibt',
    'TOEFLSPEAKINGIBT': 'toefl_speaking_ibt',
    'TOEFLLISTENINGIBT': 'toefl_listening_ibt',
    'TOEFLOVERALLPBT': 'toefl_overall_pbt',
    'DUOLINGOSCORE': 'duolingo_score',
    'PTESCORE': 'pte_score',
    'ATAR': 'atar',
    'CAESCORE': 'cae_score',
    'SATSCORE': 'sat_score',
    'ACTSCORE': 'act_score',
    'GREVERBALREASONING': 'gre_verbal_reasoning',
    'GREQUANTITATIVEREASONING': 'gre_quantitative_reasoning',
    'GREANALYTICWRITING': 'gre_analytic_writing',
    'LSATSCORE': 'lsat_score',
    'APPLICATIONFEEPAPER': 'application_fee_paper',
    'APPLICATIONFEEONLINE': 'application_fee_online',
    'APPLICATIONFEECURRENCY': 'application_fee_currency',
    'URLCOURSEINFO': 'url_course_info',
    'URLADMISSIONSPROCESSINFO': 'url_admission_info',
    'URLENGLISHBRIDGINGPROGRAMINFO': 'url_bridging_program_info',
    'URLCAREEROUTCOMES': 'url_career_outcomes',
    'URLORIENTATIONINFO': 'url_orientation_info',
    'URLPATHWAYINFO': 'url_pathway_info',
    'KEYWORDS': 'keywords',
    'DEPARTMENTNAME': 'department_name',
    'PROFESSIONALRECOGNITION': 'professional_recognition',
    'ESTIMATEDJOBROLES': 'estimated_job_roles',
    'AUSCOURSECRICOSCODE': 'cricos_code',
    'CRMID': 'crm_id',
    'ISINTERNATIONAL': 'is_international'
}

FEES_COLUMN_MAP = {
    'ProviderID': 'provider_id',
    'ProviderName': 'provider_name',
    'COURSEID': 'course_id',
    'CourseName': 'course_name',
    'YEAR': 'year',
    'UNIT': 'unit',
    'UNITPRICE': 'unit_price',
    'UNITCOUNT': 'unit_count',
    'CURRENCY': 'currency',
    'TOTALANNUALFEE': 'total_annual_fee',
    'TOTALCOURSEFEE': 'total_course_fee',
    'FeeLink': 'fee_link'
}

INTAKES_COLUMN_MAP = {
    'INTAKEID': 'intake_id',
    'PROVIDERID': 'provider_id',
    'ProviderName': 'provider_name',
    'YEAR': 'year',
    'COMMENCEMENTDATE': 'commencement_date',
    'ENDDATE': 'end_date',
    'ORIENTATIONDATE': 'orientation_date',
    'APPLICATIONDEADLINE': 'application_deadline',
    'ISOPEN': 'is_open',
    'TENTATIVE': 'tentative'
}

# All schemas in order
ALL_SCHEMAS = [
    PROVIDERS_SCHEMA,
    CAMPUS_LOCATIONS_SCHEMA,
    COURSES_SCHEMA,
    FEES_SCHEMA,
    INTAKES_SCHEMA
]

# All column mappings
ALL_COLUMN_MAPS = {
    'providers': PROVIDERS_COLUMN_MAP,
    'campus_locations': CAMPUS_LOCATIONS_COLUMN_MAP,
    'courses': COURSES_COLUMN_MAP,
    'fees': FEES_COLUMN_MAP,
    'intakes': INTAKES_COLUMN_MAP
}
