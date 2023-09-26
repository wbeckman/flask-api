from flask import Flask, request, Response

app = Flask(__name__)


@app.route('/')
def home():
    return "<p>Hello World</p>"


@app.route('/score', methods=["POST"])
def score():
    error_msg = ''
    json_req = request.get_json()
    cols = ['odor', 'stalk_root', 'stalk_surface_below_ring', 'spore_print_color']

    missing_cols = set(cols) - set(json_req.keys())

    # Invalid columns - not all input columns specified
    if len(missing_cols) != 0:
        error_msg += 'Not all columns were specified for model. Missing columns: \n\t' + '\n\t'.join(list(missing_cols)) + '\n'
    
    # Invalid feature values
    column_vals = [json_req[col].strip() if col in json_req else None for col in cols]
    valid_input = validate_input(*column_vals)
    if not all(valid_input):
        invalid_input_info = ''
        for idx, val in enumerate(column_vals):
            if not valid_input[idx] and val is not None:
                invalid_input_info += f'\n    {val} is not a valid value for {cols[idx]}'
        if invalid_input_info:
            error_msg += 'Input is invalid:' + invalid_input_info
    if error_msg:
        return Response(error_msg, status=400)

    feature_values = extract_features(*[json_req[col] for col in cols])
    return Response(response=str(int(score_input(*feature_values))), status=200)

def validate_input(odor, stalk_root, stalk_surface_below_ring, spore_print_color):
    """
    Validates that request data is within allowed categories for features. Permitted categories
    and their associated meanings are:
    
    odor	Feature	Categorical		almond=a,anise=l,creosote=c,fishy=y,foul=f, musty=m,none=n,pungent=p,spicy=s
    stalk-root	Feature	Categorical		bulbous=b,club=c,cup=u,equal=e,rhizomorphs=z,rooted=r,missing=?
    stalk-surface-below-ring	Feature	Categorical		fibrous=f,scaly=y,silky=k,smooth=s
    spore-print-color	Feature	Categorical		black=k,brown=n,buff=b,chocolate=h,green=r, orange=o,purple=u,white=w,yellow=y
    """
    odor_valid = odor in ['a', 'l', 'c', 'y', 'f', 'm', 'n', 'p', 's']
    stalk_root_valid = stalk_root in ['b','c','u','e','z','r','?']
    stalk_surface_below_ring_valid = stalk_surface_below_ring in ['f','y','k','s']
    spore_print_color_valid = spore_print_color in ['k','n','b','h','r','o','u','w','y']

    return (odor_valid, stalk_root_valid, stalk_surface_below_ring_valid, spore_print_color_valid)


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