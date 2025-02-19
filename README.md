# CureLink AI Agent
CureLink is an interactive application using a chatbot-like environment, that helps prevent, organize and manage situations that require medical attention. It can be used both by patients and doctors.

## How it works
### Symptom Analysis
User describes their symptoms in a chat-bot like environment.User's age, medical record, family history are stored in the database. The agent decides on a possible diagnosis *(based on symptoms described and medical/family record)* and then recommends a **Specialist** *(Doctor)* through OpenAI. Then the user gets asked if they will need pwd *(people with disabilities)* access. Proceeding the user will be presented with all available doctors in their area and can tell the agent to book an **appointment** for them. The agent can also decided based on the symptoms given if the user should **stay at home** *(and suggest simple at-home remedies)* or recognize an **emergency** and tell the user to visit a hospital as soon as possible. All tasks are automated and performed by the agent. User's are also able to indicate a **direct appointment** with a doctor of their liking *skipping the symptoms analysis part*.

### Patient's Appointments
Users can see their scheduled and completed appointments.

### Doctor's Scheduler
The doctor can communicate with an agent in a chat-bot like environment and **make free spaces for appointments** in the future *(by either giving the days or dates and declaring the time intervals)*. The agent takes a look in the database and adds new spaces for appointments *(only those in the future and in spaces that dont already exist)*. The doctor can also request to create an empty slot for just one day at a specific time.

### Doctor's Appointments and Feedback
Doctor can look at their appointments *(completed or scheduled)*. We consider an appointment to be completed when the doctor has given a diagnosis. Then the doctor can give *(again in a chat-bot like environment)* a **diagnosis for a patient** they examined *(so for a scheduled appointment)*. The agent then goes and updates the appointment inserting the **diagnosis** *(and possible medication prescribed)* into the database and marks the appointment as completed. If doctor gives no diagnosis the patient is flagged by the agent as healthy.

### Register/Login
User can register and login as either patients or doctors. In the future they can update their account information through the related section. *Anyone can register as a doctor, there are no checks for medical diplomas etc as this is not the purpose of the application*.

### Database
All information about patients, doctors appointments etc are stored in a database. The agent is able to update, insert and retrieve data from the database. For the purposes of this hackathon the database is filled with mocked data about doctors and patients and has pseudo-appointments.

## Tech Stack
 - **Python** $\ge$ 3.8
 - **Open AI API**
 - **Google Geocoding API**
 - **Flask** and other Python libraries
 - **MySQL** 8.0 for a structured database
 - **HTML/CSS** for a simple UI/UX

 ## Running the application
 1. Clone this repository:
 ```bash
 git clone https://github.com/chrisvobi/cureLink-netcomp-hackathon.git
 ```
 2. Navigate to the project directory:
 ```bash
 cd cureLink-netcomp-hackathon
 ```
 3. Create a `config.json` file in the root directory based on `config.sample.json`.
 ```bash
 {
    "KEY": "your openai API key",
    "GOOGLE_API_KEY": "your google API key",
    "SECRET_KEY": "a very secret key"
}
```
4. Run the following line in the project directory:
```bash
docker compose up
```
5. When the docker build finishes open a web browser and direct to `localhost:80`.

If you followed the above steps you should be able to now use the application. Mocked doctor and patients accounts will be provided to you.

## Future Expansions
- Intergrate **OpenAI Whisper** so both patients and doctors can talk *(instead of typing to the user)*.
- Make the Agent smarter and able to recognize name typos. *Currently the agent is able to catch parts of the name (if user forgets some letters or just gives first/last name) but can't recognize harder typos*.
- Expand the symptoms analysis agent to be able to suggest medical tests to the patient.

## Extra Documentation
For extra documentation on how the app works you can check our small presentation [here](CURELINK.pdf).
