import wave,math,struct,os
os.makedirs('tones',exist_ok=True)
R=22050
def tone(f,d):
    n=int(R*d)
    return [int(20000*min(1,(n-i)/(R*0.05))*math.sin(2*math.pi*f*i/R)) for i in range(n)]
def sil(d):
    return [0]*int(R*d)
def save(name,s):
    w=wave.open('tones/'+name+'.wav','wb')
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(R)
    w.writeframes(b''.join(struct.pack('<h',x) for x in s))
    w.close()
save('beep',tone(1000,.6))
save('double',tone(1000,.3)+sil(.2)+tone(1000,.3))
s=[];p=0
for i in range(R*3):
    p+=2*math.pi*(800+400*math.sin(2*math.pi*1.5*i/R))/R
    s.append(int(20000*math.sin(p)))
save('siren',s)
save('chime',tone(880,.5)+tone(1320,.5)+tone(1760,.9))
