

def create_2D_dataset(dataset1D, window_lenght):
    """ 
    create_2D_dataset(dataset1D, window_lenght, look_ahead=1)
    converts a 1D vector of values into 2D dataset a matrix required by LSTMs
    Example: 
    input vector = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    window_lenght = 2
    Gives:
    
   X = [[1, 2]  Y = [3,
         2, 3        4,
         3, 4        5,
         4, 5        6,
         5, 6        7,
         6, 7        8,
         7, 8 ]]     9]
    ≈
    """
    N_samples = dataset1D.shape[0]
    Xy = np.zeros([N_samples - window_lenght,window_lenght+1]).astype(type(dataset1D.iat[0]))
    for i in range(window_lenght+1):
        Xy[:,i] = dataset1D[i:(i+N_samples-window_lenght)]
    X =Xy[:,0:window_lenght]
    Y = Xy[:,-1]
    return X, Y


def create_3D_dataset(dataset2D, window_lenght = 10, target_variable='rel_return'):
    """ 
    Creating a 3D matrix of X data from 
    dataset2D: a data frame type of dataset (N rows,M cols)

    look_ahead: how many days ahead to make the prediction (1 means next day)
    window_lenght: How many time steps (prior days) to take int account when doing the prediction
    """
    number_of_features = dataset2D.shape[1]
    number_of_data_samples = dataset2D.shape[0]
    cols = dataset2D.columns
    X = np.zeros([(number_of_data_samples - window_lenght ), window_lenght, number_of_features])
    print("X-shape:",X.shape)

    # Formating all input features to the right matriz format
    for i,var in enumerate(cols): # for all imput variables,stack each variable X matrix in the Z dimension
        tempX, tempY = create_2D_dataset(dataset2D[var],window_lenght) 
        #print("tempX:",tempX.shape)
        X[:,:,i] = tempX
        if var==target_variable:
            Y = tempY
    return X, Y


def summarize_macd_intervals(df):
    """creates a column with the macd_diff and divides the input dataframe into smaller chunks based on the sign of the macd_diff
    Example cocde:
    summarize_macd_intervals(df_data['NVDA'].tail(300))
    """
    
    macd_diff = calculate_macd(df['Close'])
    df_out = df.copy()
    df_out['macd_diff'] = macd_diff
    # Group the dataframe by consecutive True values in the vector
    is_positive = macd_diff > 0 
    group_nr = (is_positive != np.roll(is_positive, 1)).cumsum()  # array of groups, on new group number each time the group number each time the macd changes sign 
    df_out['group_nr'] = group_nr

    # Adding MACD features of each group. Each group represents consecutive trading days where the MACD diff has the same sign + or -
    df_grouped = df_out.reset_index().groupby('group_nr').agg(
        date_first=('Date','first'),  # starting date of each group
        date_last=('Date','last'),  # ending date of each group
        duration_trade_days=('Close','count'),  # num ber of trading days in group  
        first_open=('Open','first'),  # opening price of first day in group 
        first_close=('Close','first'),  # closing price of first day in group 
        last_close=('Close','last'), # closing price of last day in group 
        min_value=('Low','min'),  # minimum value during group period to determine bottom points
        min_idx=('Low','idxmin'),
        max_value=('High','max'),  # maximum value during group period to determine top points
        max_idx=('High','idxmax'),
        macd_diff_first=('macd_diff','first'),  # ensure that the buy trigger starts with a positive diff
        macd_diff_mean=('macd_diff','mean'),  # the mean MACD diff value in the group. It should usually fluctuate from positive to negative each consecutive group
        macd_diff_max=('macd_diff','max'),
        macd_diff_min=('macd_diff','min')
        ).reset_index(drop=True)

    df_grouped['min_value_diff'] = (df_grouped['min_value'] - np.roll(df_grouped['min_value'],2)) / (df_grouped['min_idx'] - np.roll(df_grouped['min_idx'],2))/df_grouped['min_value']  # relative return difference pr day between minima roll -1 is the row after +1 the row before
    df_grouped['min_value_2diff'] = (df_grouped['min_value_diff'] - np.roll(df_grouped['min_value_diff'],4)) / (df_grouped['min_idx'] - np.roll(df_grouped['min_idx'],4)) # second order derivative of bottom points
    df_grouped['max_value_diff'] = (df_grouped['max_value'] - np.roll(df_grouped['max_value'],2)) / (df_grouped['max_idx'] - np.roll(df_grouped['max_idx'],2))/df_grouped['max_value']  # relative return difference pr day between minima roll -1 is the row after +1 the row before
    df_grouped['max_value_2diff'] = (df_grouped['max_value_diff'] - np.roll(df_grouped['max_value_diff'],4)) / (df_grouped['max_idx'] - np.roll(df_grouped['max_idx'],4)) # second order derivative of bottom points
    df_grouped['first_return_close_close'] = (df_grouped['first_close'] - np.roll(df_grouped['last_close'],1))/df_grouped['first_open']  # return first day close previous last day - close present first day 
    df_grouped['first_return_open_close'] = (df_grouped['first_close'] - df_grouped['first_open'])/df_grouped['first_open']   # return first day open - close
    df_grouped['first_return_close_open'] = (df_grouped['first_open'] - np.roll(df_grouped['last_close'],1))/df_grouped['first_open']   # return first day close previous last day - open present first day 
    df_grouped['rel_holding_gain'] = np.roll(df_grouped['first_close'],-1) / df_grouped['first_close'] # holding increase between start of current group and the first close after MACD changes sign and this group is closed
    df_grouped['rel_return'] = df_grouped['rel_holding_gain'] - 1
    df_grouped['duration_cal_days'] = (df_grouped['date_last'] - df_grouped['date_first']).dt.days.astype('int16') + 1

    return df_grouped.iloc[4:-1,:]  # removing the 4 first and last as the second order derivative is not valid for the two first samples
