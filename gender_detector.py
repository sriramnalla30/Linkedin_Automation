"""
Gender Detection for Proper Salutation (Sir/Ma'am)
Uses name-based heuristics for Indian names
"""

# Common Indian female name patterns/endings
FEMALE_INDICATORS = [
    # Common endings
    'a', 'i', 'ee', 'ita', 'ita', 'ika', 'ini', 'ani', 'ati', 'ati',
    # Common names
    'priya', 'anjali', 'pooja', 'neha', 'shreya', 'divya', 'ananya', 
    'kavya', 'riya', 'diya', 'sia', 'aisha', 'nisha', 'trisha',
    'swati', 'preeti', 'deepti', 'aarti', 'bharti', 'jyoti', 'kirti',
    'smriti', 'aditi', 'kriti', 'shruti', 'stuti', 'garima', 'anushka',
    'priyanka', 'deepika', 'karishma', 'aishwarya', 'vidya', 'padma',
    'lakshmi', 'saraswati', 'durga', 'sita', 'radha', 'meera', 'gita',
    'sunita', 'anita', 'kavita', 'savita', 'lalita', 'mamta', 'shobha',
    'usha', 'rekha', 'sudha', 'madhu', 'ragini', 'nalini', 'rohini',
    'mohini', 'yamini', 'nandini', 'chandni', 'rashmi', 'roshni',
    'shweta', 'archana', 'vandana', 'sadhana', 'kalpana', 'sanjana',
    'anjana', 'ranjana', 'monica', 'veronica', 'sonica', 'danica',
    'sneha', 'megha', 'diksha', 'sakshi', 'raksha', 'aksha', 'bhavna',
    'sapna', 'swapna', 'ratna', 'chitra', 'mitra', 'tanvi', 'manvi',
    'janvi', 'jhanvi', 'devi', 'sridevi', 'mahadevi', 'bhuvana',
    'pavana', 'ramya', 'sowmya', 'soumya', 'saumya', 'divyasri',
    'gayatri', 'savitri', 'sarojini', 'rukmini', 'vasundhara',
    'soundarya', 'arundhati', 'ashwini', 'revathi', 'vaishnavi',
    'bhargavi', 'madhavi', 'radhika', 'chandrika', 'mallika', 'ambika',
    'tanika', 'manika', 'monika', 'vani', 'rani', 'soni', 'ruchi',
    'khushi', 'tanu', 'manu', 'richa', 'shikha', 'rekha', 'lekha',
    'deeksha', 'meghna', 'rachna', 'poornima', 'kalyani', 'vasudha',
    'medha', 'nidhi', 'riddhi', 'siddhi', 'vriddhi', 'labdhi', 'shalini',
    'suman', 'poonam', 'reena', 'meena', 'seema', 'neelam', 'parveen',
    'yasmeen', 'shabnam', 'sanam', 'anam', 'zara', 'sara', 'tara',
    'hema', 'uma', 'shama', 'fatima', 'ayesha', 'zahra', 'bismita',
    'stephanie', 'jennifer', 'jessica', 'sarah', 'emily', 'emma',
    'olivia', 'sophia', 'isabella', 'mia', 'charlotte', 'amelia',
    'harper', 'evelyn', 'abigail', 'ella', 'scarlett', 'grace',
    'victoria', 'riley', 'aria', 'lily', 'aurora', 'zoey', 'nora',
    'camila', 'hannah', 'lillian', 'addison', 'eleanor', 'natalie',
    'luna', 'savannah', 'brooklyn', 'leah', 'zoe', 'stella', 'hazel',
    'ellie', 'paisley', 'audrey', 'skylar', 'violet', 'claire', 'bella',
    'lucy', 'anna', 'caroline', 'genesis', 'aaliyah', 'kennedy', 'kinsley'
]

# Common Indian male name patterns
MALE_INDICATORS = [
    'kumar', 'raj', 'deep', 'dev', 'singh', 'shankar', 'krishna', 
    'ram', 'shyam', 'mohan', 'sohan', 'rohan', 'gopal', 'kishan',
    'ravi', 'anil', 'sunil', 'kapil', 'sahil', 'rahul', 'nikhil',
    'akhil', 'ankit', 'sumit', 'amit', 'rohit', 'mohit', 'vinit',
    'puneet', 'naveen', 'praveen', 'vijay', 'sanjay', 'ajay', 'jay',
    'uday', 'abhay', 'akshay', 'aditya', 'surya', 'arjun', 'varun',
    'tarun', 'karun', 'karan', 'aryan', 'vivan', 'rehan', 'roshan',
    'kishan', 'ishan', 'eshan', 'lakshman', 'hanuman', 'balram',
    'shivam', 'param', 'uttam', 'gautam', 'satyam', 'prashant',
    'nishant', 'hemant', 'anant', 'vikrant', 'prateek', 'ritvik',
    'kartik', 'karthik', 'mayank', 'anurag', 'chirag', 'dheeraj',
    'neeraj', 'pankaj', 'manoj', 'saroj', 'ashok', 'vinod', 'pramod',
    'naresh', 'suresh', 'ramesh', 'mahesh', 'dinesh', 'ganesh', 'rajesh',
    'umesh', 'mukesh', 'rakesh', 'lokesh', 'hitesh', 'ritesh', 'jitesh',
    'alpesh', 'paresh', 'bhavesh', 'jayesh', 'kalpesh', 'yogesh',
    'harish', 'girish', 'satish', 'manish', 'danish', 'tanish', 'vansh',
    'harsh', 'sparsh', 'yash', 'prakash', 'aakash', 'vikash', 'subhash',
    'bhushan', 'darshan', 'shan', 'krishan', 'lakhan', 'rajan', 'sajan',
    'pavan', 'shravan', 'chetan', 'ketan', 'sachin', 'tushar', 'bhaskar',
    'shankar', 'omkar', 'diwakar', 'shekhar', 'abhinav', 'raghav', 'vaibhav',
    'utsav', 'saurav', 'gaurav', 'anurav', 'sameer', 'ranveer', 'tanveer',
    'jasveer', 'sukhveer', 'amrit', 'sumit', 'lalit', 'vineet', 'anoop',
    'roop', 'swaroop', 'pradeep', 'sandeep', 'kuldeep', 'dilip', 'ashish',
    'manmeet', 'harpreet', 'gurpreet', 'amandeep', 'gagandeep',
    'praseeth', 'basavaraj', 'ashok', 'john', 'michael', 'david', 'james',
    'robert', 'william', 'richard', 'joseph', 'thomas', 'charles', 'daniel',
    'matthew', 'anthony', 'mark', 'donald', 'steven', 'paul', 'andrew',
    'joshua', 'kenneth', 'kevin', 'brian', 'george', 'timothy', 'ronald'
]

# Names that are clearly one gender
KNOWN_FEMALE_NAMES = {
    'bismita', 'stephanie', 'priya', 'neha', 'pooja', 'anjali', 'sneha',
    'kavya', 'divya', 'shreya', 'ananya', 'riya', 'aisha', 'nisha',
    'trisha', 'swati', 'preeti', 'deepti', 'jyoti', 'aarti', 'smriti',
    'aditi', 'kriti', 'shruti', 'garima', 'anushka', 'priyanka', 'deepika',
    'aishwarya', 'vidya', 'lakshmi', 'meera', 'sunita', 'anita', 'kavita',
    'rekha', 'sudha', 'madhu', 'nandini', 'rashmi', 'shweta', 'archana',
    'vandana', 'sanjana', 'megha', 'diksha', 'sakshi', 'bhavna', 'sapna',
    'tanvi', 'manvi', 'janvi', 'gayatri', 'vaishnavi', 'bhargavi', 'madhavi',
    'radhika', 'mallika', 'khushi', 'richa', 'shikha', 'meghna', 'poornima',
    'medha', 'nidhi', 'riddhi', 'siddhi', 'shalini', 'poonam', 'reena',
    'meena', 'seema', 'neelam', 'jennifer', 'jessica', 'sarah', 'emily',
    'emma', 'olivia', 'sophia', 'mia', 'grace', 'victoria', 'hannah', 'anna'
}

KNOWN_MALE_NAMES = {
    'praseeth', 'basavaraj', 'ashok', 'umesh', 'ravi', 'rahul', 'rohan',
    'aditya', 'arjun', 'varun', 'karan', 'vijay', 'sanjay', 'ajay',
    'amit', 'sumit', 'rohit', 'mohit', 'ankit', 'nikhil', 'akhil',
    'mayank', 'chirag', 'dheeraj', 'pankaj', 'manoj', 'ashok', 'vinod',
    'rajesh', 'suresh', 'ramesh', 'mahesh', 'ganesh', 'dinesh', 'hitesh',
    'ritesh', 'manish', 'harish', 'satish', 'yash', 'prakash', 'vikash',
    'harsh', 'tushar', 'shankar', 'sachin', 'gaurav', 'saurav', 'sameer',
    'sandeep', 'pradeep', 'kuldeep', 'dilip', 'john', 'michael', 'david',
    'james', 'robert', 'william', 'richard', 'joseph', 'thomas', 'daniel',
    'matthew', 'anthony', 'mark', 'steven', 'paul', 'andrew', 'kevin', 'brian'
}


def detect_gender(full_name: str) -> str:
    """
    Detect gender from name and return 'male', 'female', or 'unknown'
    """
    if not full_name:
        return 'unknown'
    
    # Get first name and clean it
    first_name = full_name.strip().split()[0].lower()
    full_name_lower = full_name.lower()
    
    # Check known names first
    if first_name in KNOWN_FEMALE_NAMES:
        return 'female'
    if first_name in KNOWN_MALE_NAMES:
        return 'male'
    
    # Check for female indicators
    for indicator in FEMALE_INDICATORS:
        if first_name == indicator or first_name.endswith(indicator):
            return 'female'
    
    # Check for male indicators
    for indicator in MALE_INDICATORS:
        if first_name == indicator or indicator in full_name_lower:
            return 'male'
    
    # Default heuristics for Indian names
    # Names ending in 'a', 'i' are often female
    if first_name.endswith(('a', 'i', 'ee')) and len(first_name) > 3:
        # But some male names also end in 'a' like Krishna, Surya
        male_exceptions = ['krishna', 'surya', 'indra', 'rudra', 'chandra', 'raja']
        if first_name not in male_exceptions:
            return 'female'
    
    # Names ending in consonants or specific patterns are often male
    if first_name.endswith(('sh', 'j', 'k', 'n', 'r', 'm', 'p', 'v', 't', 'l', 'd')):
        return 'male'
    
    return 'unknown'


def get_salutation(full_name: str, gender: str = None) -> str:
    """
    Get appropriate salutation (Sir/Ma'am) based on gender
    """
    if gender is None:
        gender = detect_gender(full_name)
    
    if gender == 'female':
        return "Ma'am"
    elif gender == 'male':
        return "Sir"
    else:
        # Default to Sir for unknown (you can change this)
        return "Sir"


def get_first_name(full_name: str) -> str:
    """Extract first name from full name"""
    if not full_name:
        return ""
    return full_name.strip().split()[0]


# Test the gender detection
if __name__ == "__main__":
    test_names = [
        "Praseeth VM",
        "Basavaraj C",
        "Ashok C",
        "Bismita Deka",
        "Stephanie Garcia",
        "Umesh Sachdev",
        "Ravi Mayuram",
        "Priya Sharma",
        "Rahul Kumar",
        "Neha Singh"
    ]
    
    print("Gender Detection Test:")
    print("-" * 50)
    for name in test_names:
        gender = detect_gender(name)
        salutation = get_salutation(name)
        first = get_first_name(name)
        print(f"{name:25} -> {gender:8} -> {first} {salutation}")
