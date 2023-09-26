from flask import Flask, request, Response
from collections import OrderedDict

app = Flask(__name__)


@app.route('/')
def home():
    return "<p>Hello World</p>"

@app.route('/score', methods=["POST"])
def score():
    error_msg = ''
    raw_column_data = request.get_json()
    required_cols = ['odor', 'stalk_root', 'stalk_surface_below_ring', 'spore_print_color']
    column_data_relevant = get_relevant_column_data(raw_column_data, required_cols)
    missing_cols = get_missing_cols(required_cols, column_data_relevant.keys())

    # Generate missing column error message
    if missing_cols: error_msg += missing_col_error_msg(missing_cols)

    # Check for valid feature values
    validity_check = validate_input(column_data_relevant, required_cols, validity_fn)
    if not all(validity_check.values()):
        error_msg += invalid_input_error_msg(validity_check, column_data_relevant)

    if error_msg: # If there are any errors, return error message with 400 response
        return Response(error_msg, status=400)

    feature_values = extract_features(*column_data_relevant.values())
    return Response(response=str(int(score_input(*feature_values))), status=200)

def get_relevant_column_data(json_request, required_columns):
    """Returns only relevant data columns from the request for model scoring"""
    rtn = OrderedDict()
    for col in required_columns:
        if col in json_request:
            rtn[col] = json_request[col]
    return rtn

def get_missing_cols(input_cols, required_cols):
    """Determines missing input cols for model"""
    return set(input_cols) - set(required_cols)

def missing_col_error_msg(missing_cols):
    """Generates error message based on missing columns"""
    return 'Not all columns were specified for model. Missing columns: \n\t' \
        + '\n\t'.join(list(missing_cols)) + '\n'

def validity_fn(attribute, value):
    """
    Determine validity for an attribute and corresponding value for that attribute.
    
    Permitted categories and their associated meanings are:
    odor	Feature	Categorical		almond=a,anise=l,creosote=c,fishy=y,foul=f, musty=m,none=n,pungent=p,spicy=s
    stalk-root	Feature	Categorical		bulbous=b,club=c,cup=u,equal=e,rhizomorphs=z,rooted=r,missing=?
    stalk-surface-below-ring	Feature	Categorical		fibrous=f,scaly=y,silky=k,smooth=s
    spore-print-color	Feature	Categorical		black=k,brown=n,buff=b,chocolate=h,green=r, orange=o,purple=u,white=w,yellow=y
    """
    validity_map = {
        'odor': ['a', 'l', 'c', 'y', 'f', 'm', 'n', 'p', 's'],
        'stalk_root': ['b','c','u','e','z','r','?'],
        'stalk_surface_below_ring': ['f','y','k','s'],
        'spore_print_color': ['k','n','b','h','r','o','u','w','y']
    }

    return attribute in validity_map and value in validity_map[attribute]

def validate_input(data, required_cols, validity_fn):
    """
    General function to validate data based on the data provided, the columns required,
    and a validity function that takes in the current attribute/value.
    """
    rtn = {}

    for col in required_cols:
        if col in data:
            rtn[col] = validity_fn(col, data[col])
    return rtn
    
def invalid_input_error_msg(validity_check, data):
    """Generates error message for invalid input (e.g. bad column values)"""
    invalid_input_info = ''
    for k,v in validity_check.items():
        if not v:
            val = data[k]
            invalid_input_info += f'\n    "{val}" is not a valid value for "{k}"'
    return 'Input is invalid:' + invalid_input_info

def extract_features(odor, stalk_root, stalk_surface_below_ring, spore_print_color):
    """
    Turns categorical features into features that we care about for our model. Realistically,
    this would probably be much more complex and would be done in a feature store.
    """
    return (
        int(odor == 'n'), int(stalk_root == 'c'), int(stalk_surface_below_ring == 'y'),
        int(spore_print_color == 'r'), int(odor == 'a'), int(odor == 'l')
    )

def score_input(odor_n, stalk_root_c, stalk_surface_below_ring_y, spore_print_color_r, odor_a, odor_l):
    """Function to mimic behavior of pre-trained decision tree from scikit-learn"""
    if odor_n <= 0.5:
        if stalk_root_c <= 0.5:
            if stalk_surface_below_ring_y <= 0.5:
                if odor_a <= 0.5:
                    if odor_l <= 0.5:
                        return True
                    else:  # if odor_l > 0.5
                        return False
                else:  # if odor_a > 0.5
                    return False
            else:  # if stalk_surface_below_ring_y > 0.5
                return False
        else:  # if stalk_root_c > 0.5
            if stalk_surface_below_ring_y <= 0.5:
                return False
            else:  # if stalk_surface_below_ring_y > 0.5
                return True
    else:  # if odor_n > 0.5
        if spore_print_color_r <= 0.5:
            if stalk_surface_below_ring_y <= 0.5:
                return False
            else:  # if stalk_surface_below_ring_y > 0.5
                if stalk_root_c <= 0.5:
                    return True

                else:  # if stalk_root_c > 0.5
                    return True
        else:  # if spore_print_color_r > 0.5
            return True