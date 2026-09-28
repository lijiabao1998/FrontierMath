#include <stdio.h>
#define  MARK  'o'
#define  FREE  '.'
#define  SYMM  ".:/-xo+*c"
#define  Topos(zei)  ( (zei) - ( (zei)< 'A'-1 ? '0' : 'A'-1-10 ))
#define  TOPOS(zei)  ( (zei) - ( (zei)>='0'&&(zei)<='9' ? '0' : ( (zei)>='A'&&(zei)<='Z' ? 'A'-10 : ( (zei)>='a'&&(zei)<='z' ? 'a'-36 : (zei)+1 ) ) ) )
#define  MAX_N  62

char  *symclass[10] = { "iden","rot2","dia1","ort1","dia2","rot4","ort2","full","rct4", "????" };

main(argc,argv)
int  argc;
char  *argv[];
{
register  i, j, h, k, no = 0, new;
char  buffer[2*MAX_N+4], line[2*MAX_N+1];
FILE  *fp = (argc>1 ? fopen(argv[1],"r") : stdin);
if (!fp)  return  fprintf(stderr,"Can't open %s\n",argv[1]), -1;
while (fgets(buffer,2*MAX_N+4,fp))
{  h = 0;
   no++;
   for (i=0;buffer[i];i++)
	  if (buffer[i]=='@')  break;
   new = !buffer[i];
   for (i=new;buffer[i];i++)
	  if (i >= 2*MAX_N+2)
         return  fprintf(stderr,"N is larger than %d in line %d\n",MAX_N,no), -1;
      else if (buffer[i]=='\n')  break;
      else if (buffer[i] < '0')
         return  fprintf(stderr,"Illegal character in line %d\n",no), -1;
      else if (buffer[i] > h)
		 h = buffer[i];
   if (h)
      h = (new ? TOPOS(h)+1 : Topos(h)+1);
   else
   {
#ifdef  SIMPLE
      printf("N=0\n");
#else
      for (j=0;j<8;j++)
	     if (buffer[0]==SYMM[j])
            break;
      printf("%3u. L\366sung:     Sym.-Gruppe  %s\n",no,symclass[j]);
#endif
	  continue;
   }
   i-=new;
   if (i&1)
      return  fprintf(stderr,"Odd number of characters in line %d\n",no), -1;
   else if (h+h != i)
      return  fprintf(stderr,"The number of characters is 2*%d != %d in line %d\n",i/2,2*h,no), -1;
   for (j=0;j<i;j++)
      line[j] = ((j&1) ? ' ' : FREE);
   line[j-1] = '\n';
   line[j] = '\0';
#ifdef  SIMPLE
   printf("N=%2d\n",i/2);
#else
   for (j=0;j<8;j++)
	  if (buffer[0]==SYMM[j])
         break;
   printf("%3u. L\366sung:     Sym.-Gruppe  %s\n",no,symclass[j]);
#endif
   h = k = 0;
   for (j=new;j<i;j+=2)
   {  line[h+h] = FREE;
      line[k+k] = FREE;
      h = (new ? TOPOS(buffer[j]) : Topos(buffer[j]) );
      line[h+h] = MARK;
      k = (new ? TOPOS(buffer[j+1]) : Topos(buffer[j+1]) );
      line[k+k] = MARK;
      printf(" %s",line);  /* must start with SPACE for compatibility */
   }
}
fclose(fp);
if (fp != stdin)
   fprintf(stderr,"%d solutions decoded\n",no);
return(0);
}
